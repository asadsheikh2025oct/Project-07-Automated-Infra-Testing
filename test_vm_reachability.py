#!/usr/bin/env python3
"""
VM Reachability Test
Tests that the deployed VM is accessible and has SSH port open
"""
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
    """Test that SSH port 22 is open and accepting connections"""
    try:
        print(f"Testing SSH connection to {ip_address}:22...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip_address, port))
        sock.close()
        
        if result == 0:
            print(f"✅ PASS: SSH port {port} is open and accepting connections")
            return True
        else:
            print(f"❌ FAIL: SSH port {port} is not accessible (error code: {result})")
            return False
    except socket.timeout:
        print(f"❌ FAIL: Connection to {ip_address}:{port} timed out after {timeout} seconds")
        return False
    except socket.gaierror as e:
        print(f"❌ FAIL: DNS resolution failed: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("VM Reachability Tests")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Check if IP variable is set
    print("\nTest 1: VM IP Variable")
    print("-" * 60)
    ip_test_passed, vm_ip = test_ip_variable()
    all_passed = all_passed and ip_test_passed
    
    # Test 2: Check SSH connectivity (only if we have an IP)
    if vm_ip:
        print("\nTest 2: SSH Port Connectivity")
        print("-" * 60)
        ssh_test_passed = test_ssh_port(vm_ip)
        all_passed = all_passed and ssh_test_passed
    else:
        print("\nTest 2: SSH Port Connectivity")
        print("-" * 60)
        print("⏭️  SKIP: Cannot test SSH connectivity without a valid IP")
        all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
