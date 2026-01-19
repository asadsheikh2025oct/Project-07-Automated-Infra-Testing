Describe "Infrastructure Integration Test" {
    $ip = $env:VM_IP

    It "Should have received a valid IP from the Deploy stage" {
        $ip | Should -Not -BeNullOrEmpty
    }

    It "Should be listening on SSH Port 22" {
        # This .NET method works on both Windows and Linux agents
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        try {
            $connect = $tcpClient.BeginConnect($ip, 22, $null, $null)
            $wait = $connect.AsyncWaitHandle.WaitOne(5000, $false) # 5 second timeout
            
            $wait | Should -Be $true
            $tcpClient.Connected | Should -Be $true
        }
        finally {
            $tcpClient.Close()
        }
    }
}