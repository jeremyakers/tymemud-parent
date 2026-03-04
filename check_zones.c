#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    FILE *f = fopen("lib/etc/builderport.token", "r");
    char token[64] = "test";
    if (f) {
        fgets(token, sizeof(token), f);
        token[strcspn(token, "\n")] = 0;
        fclose(f);
    }
    
    printf("Token: %s\n", token);
    
    // Check zones
    char cmd[512];
    snprintf(cmd, sizeof(cmd), 
        "(echo 'hello %s 1'; "
        "echo 'wld_list RANGE 0 20'; "
        "echo 'quit') | nc -w 5 127.0.0.1 9697",
        token);
    
    printf("\n=== Zone list ===\n");
    system(cmd);
    
    return 0;
}
