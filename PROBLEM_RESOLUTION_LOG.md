# Azure Pipeline VM Reachability Testing - Problem Resolution Log

## Summary
Infrastructure-as-Code testing pipeline that deploys a VM via Bicep and validates it's reachable via SSH port 22.

---

## Problems Encountered

### Problem 1: VM_IP Variable Was Empty in Pester Tests
**Symptoms:**
```
[-] Infrastructure Integration Test.Should have received a valid IP from the Deploy stage
Expected a value, but got $null or empty.
at $ip | Should -Not -BeNullOrEmpty, /home/vsts/work/1/s/VMReachability.Tests.ps1:5
```

**Root Cause:**
PowerShell variable scoping issue. The environment variable `$env:VM_IP` was not accessible inside Pester's `Describe` block execution context.

**Original Code (Broken):**
```powershell
Describe "Infrastructure Integration Test" {
    $ip = $env:VM_IP  # ❌ Runs in isolated Pester scope
    
    It "Should have received a valid IP from the Deploy stage" {
        $ip | Should -Not -BeNullOrEmpty
    }
}
```

---

### Problem 2: SSH Port 22 Not Accessible
**Symptoms:**
```
✅ PASS: VM_IP is set to: 20.162.37.151
❌ FAIL: SSH port 22 is not accessible (error code: 11)
```

**Root Cause:**
Bicep template was missing Network Security Group (NSG) rules to allow inbound SSH traffic on port 22.

**Original Bicep (Incomplete):**
- Had Public IP ✅
- Had VNet and Subnet ✅
- Had Network Interface ✅
- Had Virtual Machine ✅
- **Missing NSG with SSH allow rule** ❌

---

## Failed Solutions

### Failed Solution 1: Fix Pester Variable Scope (Attempt 1)
**Approach:** Modified YAML to add debug output and ensured `env:` section was properly configured.

**What We Tried:**
```yaml
env:
  VM_IP: $(VM_IP) # Injects the variable into the Pester environment
```

**Result:** ❌ Failed
- Debug showed variable was being passed to the PowerShell task
- But Pester still couldn't access it internally
- Variable scoping issue remained

---

### Failed Solution 2: Fix Pester Variable Scope (Attempt 2)
**Approach:** Read environment variable into script-scoped variable before `Describe` block.

**What We Tried:**
```powershell
# Read BEFORE the Describe block
$script:ip = $env:VM_IP

Describe "Infrastructure Integration Test" {
    It "Should have received a valid IP from the Deploy stage" {
        $script:ip | Should -Not -BeNullOrEmpty
    }
}
```

**Result:** ❌ Failed
- Still had scoping issues
- PowerShell on Linux with Pester 5.x had environment variable inheritance problems
- User requested alternative to PowerShell/Pester

---

## Successful Solutions

### Solution 1: Replace PowerShell/Pester with Python Testing Framework

**Changes Made:**

#### A. Created Python Test Script (`test_vm_reachability.py`)
```python
#!/usr/bin/env python3
import os
import socket
import sys

def test_ip_variable():
    """Test that VM_IP environment variable is set"""
    vm_ip = os.environ.get('VM_IP')
    
    if not vm_ip:
        print("❌ FAIL: VM_IP environment variable is not set")
        return False, None
    
    print(f"✅ PASS: VM_IP is set to: {vm_ip}")
    return True, vm_ip

def test_ssh_port(ip_address, port=22, timeout=5):
    """Test that SSH port 22 is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip_address, port))
        sock.close()
        
        if result == 0:
            print(f"✅ PASS: SSH port {port} is open")
            return True
        else:
            print(f"❌ FAIL: SSH port {port} not accessible (error: {result})")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False
```

**Why This Worked:**
- ✅ Python's `os.environ.get()` directly accesses environment variables
- ✅ No scope issues like PowerShell
- ✅ Native socket library for connectivity testing
- ✅ Clear, readable output
- ✅ Works identically on Linux/Windows/macOS

#### B. Updated Pipeline to Use Bash + Python

**Deploy Stage:**
```yaml
- bash: |
    echo '$(deploymentOutputs)'
    
    # Extract IP using jq (pre-installed on Ubuntu agents)
    VM_IP=$(echo '$(deploymentOutputs)' | jq -r '.vmIpAddress.value')
    
    echo "The VM IP captured is: $VM_IP"
    echo "##vso[task.setvariable variable=VM_IP;isOutput=true]$VM_IP"
  name: CaptureVMIP
  displayName: 'Capture VM IP Address'
```

**Test Stage:**
```yaml
- bash: |
    echo "VM_IP variable value: $(VM_IP)"
    chmod +x test_vm_reachability.py
    python3 test_vm_reachability.py
  displayName: 'Run VM Reachability Tests'
  env:
    VM_IP: $(VM_IP)
```

**Result:** ✅ Partially Successful
- Variable passing worked perfectly
- IP was correctly captured and passed
- BUT SSH connectivity test failed (revealed Problem 2)

---

### Solution 2: Add Network Security Group to Bicep Template

**Changes Made:**

#### A. Added NSG Resource
```bicep
resource nsg 'Microsoft.Network/networkSecurityGroups@2023-09-01' = {
  name: '${vmName}-nsg'
  location: location
  properties: {
    securityRules: [
      {
        name: 'AllowSSH'
        properties: {
          priority: 1000
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '22'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
          description: 'Allow SSH traffic for testing'
        }
      }
    ]
  }
}
```

#### B. Associated NSG with Subnet
```bicep
resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: '${vmName}-vnet'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: ['10.0.0.0/16']
    }
    subnets: [
      {
        name: 'default'
        properties: {
          addressPrefix: '10.0.1.0/24'
          networkSecurityGroup: {
            id: nsg.id  // ← Critical: Links NSG to subnet
          }
        }
      }
    ]
  }
}
```

**Result:** ✅ Fully Successful
- NSG created with SSH allow rule
- Port 22 became accessible from the internet
- Python tests passed completely
- Pipeline ran successfully end-to-end

---

## Final Working Solution Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Pipeline                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Stage 1: Deploy                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 1. Deploy Bicep Template                              │  │
│  │    - Create Public IP                                 │  │
│  │    - Create NSG with SSH rule (port 22)              │  │
│  │    - Create VNet + Subnet (with NSG attached)        │  │
│  │    - Create Network Interface                         │  │
│  │    - Create Ubuntu VM                                 │  │
│  │                                                        │  │
│  │ 2. Capture VM IP (Bash)                              │  │
│  │    - Parse JSON output with jq                        │  │
│  │    - Extract vmIpAddress.value                        │  │
│  │    - Set output variable for next stage               │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│              (VM_IP variable passed)                         │
│                          ↓                                   │
│  Stage 2: Test                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 1. Receive VM_IP variable                            │  │
│  │                                                        │  │
│  │ 2. Run Python Tests                                   │  │
│  │    Test 1: Verify VM_IP is not empty                 │  │
│  │    Test 2: Test TCP connection to IP:22              │  │
│  │                                                        │  │
│  │ 3. Publish JUnit Test Results                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

### What Didn't Work
1. **PowerShell/Pester** - Variable scoping issues on Linux agents
2. **Missing NSG** - Azure blocks all inbound traffic by default

### What Worked
1. **Python for testing** - Simpler, more reliable environment variable handling
2. **Bash for scripting** - Native Linux tooling (jq, bash) more stable than PowerShell on Ubuntu
3. **NSG with explicit rules** - Azure requires explicit allow rules for inbound traffic

### Best Practices Learned
- ✅ Use native Linux tools (Bash, Python) on Ubuntu agents instead of PowerShell
- ✅ Always include NSG rules when deploying VMs that need external access
- ✅ Add debug output to verify variable passing between pipeline stages
- ✅ Use Python's socket library for simple connectivity tests
- ✅ Test infrastructure testing pipelines incrementally (variables first, then connectivity)

---

## Files in Final Solution

1. **main.bicep** - Bicep template with NSG rules
2. **test_vm_reachability.py** - Python test script
3. **azure-pipelines.yml** - Pipeline using Bash + Python
4. ~~VMReachability.Tests.ps1~~ - Deprecated, replaced by Python

---

## Timeline

1. **Initial Problem**: Pester tests failing with empty VM_IP variable
2. **First Debug**: Added logging, confirmed variable passing issue
3. **Attempted Fix 1**: Modified Pester scope - Failed
4. **Attempted Fix 2**: Used script-scoped variables - Failed
5. **Paradigm Shift**: Switched from PowerShell to Python - Revealed NSG issue
6. **Final Fix**: Added NSG rules to Bicep - Complete Success ✅

---

## Success Criteria Met

✅ VM deploys automatically via Bicep  
✅ VM IP is captured and passed between pipeline stages  
✅ SSH port 22 is accessible from external sources  
✅ Automated tests verify connectivity  
✅ Pipeline reports test results in Azure DevOps  
✅ Pipeline fails if VM is not reachable  

---

**Total Time to Resolution:** Multiple iterations across 2 problem domains
**Final Status:** ✅ PIPELINE RUNNING SUCCESSFULLY
