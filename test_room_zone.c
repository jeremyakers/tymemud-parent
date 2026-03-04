#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netdb.h>

int main() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr = {AF_INET, htons(9697)};
    inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr);
    
    if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("connect");
        return 1;
    }
    
    char buf[4096];
    read(sock, buf, sizeof(buf));
    
    // Auth
    char token[64];
    FILE *f = fopen("lib/etc/builderport.token", "r");
    if (f) {
        fgets(token, sizeof(token), f);
        fclose(f);
        token[strcspn(token, "\n")] = 0;
    }
    
    char cmd[256];
    snprintf(cmd, sizeof(cmd), "hello %s 1\r\n", token);
    write(sock, cmd, strlen(cmd));
    read(sock, buf, sizeof(buf));
    
    // Create room
    snprintf(cmd, sizeof(cmd), "room_full 1298 12 3 10 10 0 VGVzdFJvb20- VGVzdERlc2M-\r\n");
    write(sock, cmd, strlen(cmd));
    read(sock, buf, sizeof(buf));
    
    // Dump room to see zone info
    write(sock, "wld_dump 1298\r\n", 16);
    memset(buf, 0, sizeof(buf));
    read(sock, buf, sizeof(buf));
    printf("wld_dump response: %s\n", buf);
    
    // Load zone 12
    write(sock, "wld_load 12\r\n", 13);
    memset(buf, 0, sizeof(buf));
    int n;
    while ((n = read(sock, buf, sizeof(buf))) > 0) {
        printf("%.*s", n, buf);
        if (strstr(buf, "END")) break;
        memset(buf, 0, sizeof(buf));
    }
    
    write(sock, "quit\r\n", 6);
    close(sock);
    return 0;
}
