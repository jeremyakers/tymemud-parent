#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main() {
    FILE *f = fopen("lib/etc/builderport.token", "r");
    char token[64] = "test";
    if (f) {
        fgets(token, sizeof(token), f);
        token[strcspn(token, "\n")] = 0;
        fclose(f);
    }
    
    char cmd[512];
    
    // Test 1: Create room and immediately check real_room
    snprintf(cmd, sizeof(cmd), 
        "(echo 'hello %s 1'; "
        "echo 'room_full 1299 12 3 10 10 0 VGVzdFJvb20- VGVzdERlc2M-'; "
        "echo 'wld_dump 1299'; "
        "echo 'wld_load 12'; "
        "echo 'quit') | nc -w 10 127.0.0.1 9697 | grep -E 'DATA|OK|ERROR'",
        token);
    
    printf("=== Test: Create room 1299 and check zone listing ===\n");
    system(cmd);
    
    return 0;
}
