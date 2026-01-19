Describe "Infrastructure Integration Test" {
    
    # We retrieve the IP address from the environment variable set by the pipeline
    $ip = $env:VM_IP

    It "Should have a valid Public IP address assigned" {
        $ip | Should -Not -BeNullOrEmpty
    }

    It "Should respond to a Ping (ICMP)" {
        $ping = Test-Connection -ComputerName $ip -Count 1 -Quiet
        $ping | Should -Be $true
    }

    It "Should be listening on SSH Port 22" {
        # This checks if the firewall and OS are actually accepting connections
        $connection = Test-NetConnection -ComputerName $ip -Port 22
        $connection.TcpTestSucceeded | Should -Be $true
    }
}