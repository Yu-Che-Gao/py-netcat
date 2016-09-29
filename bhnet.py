# -*- coding: utf-8 -*-
import sys
import socket
import getopt
import threading
import subprocess

# global variable
listen=False
command=False
upload=False
execute=""
target=""
uploadDestination=""
port=0

def usage():
    print "BHP Net Tool"
    print
    print "method: bhpnet.py -t target_host -p port"
    print "-l --listen             - 在 [host]:[port] 監聽連入連線"
    print "-e --execute            - 接到連線時執行指定檔案"
    print "-c --command            - 啟動命令列 shell"
    print "-u --upload=destination - 接到連線時上傳檔案並寫出 [destination]"
    print
    print
    print " example:"
    print "     bhpnet.py -t 192.168.0.1 -p 5555 -l -c"
    print "     bhpnet.py -t 192.168.0.1 -p 5555 -l -u=C:\\target.exe"
    print "     bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\""
    print "     echo 'ABCDEFGHI' | ./bhpnet.py -t 192.168.11.12 -p 135"

def client_handler(clientSocket):
    global upload
    global execute
    global command

    if len(uploadDestination):
        fileBuffer=""
        while True:
            data=clientSocket.recv(1024)

            if not data:
                break
            else:
                fileBuffer += data
        
        try:
            fileDescriptor=open(uploadDestination, "wb")
            fileDescriptor.write(fileBuffer)
            fileDescriptor.close()

            clientSocket.send("Successfully saved file to %s\r\n" % uploadDestination)
        except:
            clientSocket.send("Failed to save file to %s\r\n" % uploadDestination)
    
    # 檢查執行指令
    if len(execute):
        output=run_command(execute)
        clientSocket.send(output)

    # 如果要求shell，就進入另一個迴圈
    if command:
        while True:
            clientSocket.send("<BHP:#> ")
            cmdBuffer=""
            while "\n" not in cmdBuffer:
                cmdBuffer += clientSocket.recv(1024)

            response=run_command(cmdBuffer)
            clientSocket.send(response)

def server_loop():
    global target
    if not len(target):
        target="0.0.0.0"

    server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while True:
        clientSocket, addr=server.accept()

        # 啟動一個thread處理新用戶端
        clientThread=threading.Thread(target=client_handler, args=(clientSocket))
        clientThread.start()

def run_command(command):
    command=command.rstrip()
    try:
        output=subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output=" 指令執行失敗\r\n"
    
    return output

def client_sender(buffer):
    client=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((target, port))
        if len(buffer):
            client.send(buffer)
        
        while True:
            # 監聽資料回傳
            recvLen=1
            response=""

            while recvLen:
                data=client.recv(4096)
                recvLen=len(data)
                response += data

                if recvLen<4096:
                    break

            print response

            buffer=raw_input("")
            buffer += "\n"

            client.send(buffer)

    except:
        print "[*] Exception! Existing"
        client.close()

def main():
    global listen
    global port
    global execute
    global command
    global uploadDestination
    global target

    if not len(sys.argv[1:]):
        usage()

    # 讀入命令列選項
    try:
        opts, args=getopt.getopt(sys.argv[1:], "hle:t:p:cu:", ["help", "listen", "execute", "target", "port", "command", "upload"])

    except getopt.GetoptError as err:
        print str(err)
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in("-l", "--listen"):
            listen=True
        elif o in("-e", "--execute"):
            execute=a
        elif o in("-c", "--commandshell"):
            command=True
        elif o in("-u", "--upload"):
            uploadDestination=a
        elif o in("-t", "--target"):
            target=a
        elif o in("-p", "--port"):
            port=int(a)
        else:
            assert False, "選項未處理"

    # 我們要監聽，還是只是要送資料
    if not listen and len(target) and port>0:
        # 從命令列讀入buffer
        # 這會block，所以如果沒有要透過stdin傳資料的話
        # 要按ctrl-D

        buffer=EOF

        # 把資料送出去
        client_sender(buffer)

    # 上傳東西，執行指令，或是提供shell
    if listen:
        server_loop()

main()