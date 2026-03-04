<?php
// Debug script to trace what PHP sends to MUD
require_once '/home/jeremy/tymemud/_agent_work/wld_editor_api_agent/public_html/wld_editor_config.php';

function debug_status_port($commands) {
    global $status_port;
    $fp = @fsockopen('127.0.0.1', $status_port, $errno, $errstr, 5);
    if (!$fp) return [false, "connect failed"];
    
    stream_set_timeout($fp, 5);
    
    // Send all commands
    $cmd_str = implode("\r\n", $commands) . "\r\n";
    echo "Sending commands:\n" . str_replace("\r\n", "\n", $cmd_str) . "\n";
    
    fwrite($fp, $cmd_str);
    
    // Read response
    $out = '';
    while (!feof($fp)) {
        $chunk = fread($fp, 8192);
        if ($chunk === false) break;
        $out .= $chunk;
        // Break after we get END or quit response
        if (strpos($out, "END") !== false && strpos($out, "quit") !== false) {
            sleep(0.1);
            break;
        }
    }
    fclose($fp);
    
    return [true, $out];
}

// Simulate what the PHP API sends
$lines = [
    "hello c1gtri32 1",
    "tx_begin ZONES 10",
    "room_full 1000 10 1 10 10 0 QmVnaW5uaW5nIFJvb20A VGhpcyBpcyBhbiBlbXB0eSB6b25lLg0KRHVyZW4gYWRkZWQgYSB0ZXN0IGhlcmUu",
    "tx_commit",
    "quit"
];

[$ok, $resp] = debug_status_port($lines);
echo "Response:\n" . str_replace("\r\n", "\n", $resp) . "\n";
?>