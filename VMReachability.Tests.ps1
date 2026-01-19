# Read the environment variable OUTSIDE the Describe block
# This ensures it's captured before Pester creates its test scope
$script:ip = $env:VM_IP

Describe "Infrastructure Integration Test" {
    It "Should have received a valid IP from the Deploy stage" {
        $script:ip | Should -Not -BeNullOrEmpty
    }

    It "Should be listening on SSH Port 22" {
        # This .NET method works on both Windows and Linux agents
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        try {
            $connect = $tcpClient.BeginConnect($script:ip, 22, $null, $null)
            $wait = $connect.AsyncWaitHandle.WaitOne(5000, $false) # 5 second timeout
            
            $wait | Should -Be $true
            $tcpClient.Connected | Should -Be $true
        }
        finally {
            $tcpClient.Close()
        }
    }
}