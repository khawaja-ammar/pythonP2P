import socket
import _thread
import time
import os

ip = "127.0.0.1"


class node:
    global ip

    port_nu = ""
    succ_port = ""
    pred_port = ""
    hash_val = ""
    finger_table = [""] * 5

    def hash_function(self, string):
        string = str(string)
        code = 0
        size = len(string)
        for i in range(0, size):
            code = code ^ ((code << 5) + (code >> 2) + ord(string[i]))
        return code % 37

    def find_node(self, file_hash, q=True):
        lisst = {}
        blah = []
        for num in self.finger_table:
            temp = self.hash_function(num)
            lisst[temp] = num
            blah.append(temp)
        for num in blah:
            if num == file_hash:
                return lisst[num]

        x = min(blah)
        y = max(blah)

        if file_hash <= x:
            if q:
                return lisst[y]
            else:
                return lisst[x]

        elif file_hash >= y:
            return lisst[y]

        elif int(self.hash_val) < file_hash and blah[0] > file_hash:
            return lisst[blah[0]]

        else:
            for num in range(0, 4):
                a = blah[num]
                b = blah[num + 1]

                if int(a) < file_hash and int(b) >= file_hash:
                    return lisst[a]

    def join(self, port):
        sock = socket.socket()
        while 1:
            try:
                sock.connect((ip, int(port)))
                break
            except:
                print("ERROR: There is no network on this port")
                port = input("Enter port number: ")

        sock.send(("join").encode())
        sock.recv(1024).decode()
        sock.send(self.port_nu.encode())
        sock.close()

        sock = socket.socket()
        sock.bind((ip, int(self.port_nu)))
        sock.listen(1)

        client, addr = sock.accept()

        self.succ_port = client.recv(1024).decode()
        if self.succ_port == "Collision":
            print("ERROR: HASH VALUE COLLSION; Exiting")
            exit()
        client.send("ok".encode())
        self.pred_port = client.recv(1024).decode()
        client.close()
        sock.close()

        print("CONNECTED")
        print(
            "==========================================================================================="
        )

    def listen(self, client, addr):
        string = (client.recv(1024)).decode()
        sock = socket.socket()

        if string == "join":
            client.send(("ok").encode())
            to_join = (client.recv(1024)).decode()
            to_join_hash = self.hash_function(to_join)
            succ_hash = self.hash_function(str(self.succ_port))
            pred_hash = self.hash_function(str(self.pred_port))

            if int(self.hash_val) == to_join_hash:
                sock.connect((ip, int(to_join)))
                sock.send("Collision".encode())
                sock.close()

            elif self.succ_port == self.port_nu:
                sock.connect((ip, int(to_join)))
                sock.send(self.port_nu.encode())
                sock.recv(1024).decode()
                sock.send(self.port_nu.encode())
                self.succ_port = int(to_join)
                self.pred_port = int(to_join)
                sock.close()

            elif (
                (int(self.hash_val) < to_join_hash and succ_hash > to_join_hash)
                or (int(self.hash_val) < to_join_hash and self.hash_val > succ_hash)
                or (
                    int(self.hash_val) > to_join_hash
                    and self.hash_val > succ_hash
                    and to_join_hash < succ_hash
                )
            ):
                sock.connect((ip, int(to_join)))
                sock.send(str(self.succ_port).encode())
                sock.recv(1024).decode()
                sock.send(str(self.port_nu).encode())
                sock.close()
                sock = socket.socket()
                sock.connect((ip, int(self.succ_port)))
                sock.send("pred_update".encode())
                sock.recv(1024)
                sock.send(to_join.encode())
                sock.close()
                self.succ_port = int(to_join)

            else:
                # print("coming here\n")
                right_port_num = self.find_node(to_join_hash)
                # print(int(right_port_num))
                sock.connect((ip, int(right_port_num)))
                # print("blah")
                sock.send(("join").encode())
                sock.recv(1024).decode()
                sock.send(to_join.encode())
                sock.close()

        elif string == "pred_update":
            client.send("ok".encode())
            self.pred_port = client.recv(1024).decode()

        elif string == "find_file":
            client.send(("ok").encode())
            file_hash = int((client.recv(1024)).decode())
            client.send("ok".encode())
            address = (client.recv(1024)).decode()
            pred_hash = self.hash_function(str(self.pred_port))
            succ_hash = self.hash_function(str(self.succ_port))

            if (
                (int(self.hash_val) >= file_hash and self.hash_val < pred_hash)
                or (
                    int(self.hash_val) >= file_hash
                    and (pred_hash < file_hash or pred_hash > self.hash_val)
                    and (self.hash_val < succ_hash or file_hash > succ_hash)
                )
                or (
                    int(self.hash_val) < file_hash
                    and self.hash_val > pred_hash
                    and self.hash_val > succ_hash
                )
            ):
                client.send(str(self.port_nu).encode())
                client.recv(1024)
                client.send(str(self.succ_port).encode())
            else:
                right_port_num = self.find_node(file_hash, False)
                # print("blah")
                sock = socket.socket()
                sock.connect((ip, int(right_port_num)))
                sock.send(("find_file").encode())
                sock.recv(1024).decode()
                sock.send((str(file_hash)).encode())
                sock.recv(1024).decode()
                sock.send(address.encode())
                connect_with = sock.recv(1024).decode()
                sock.send("ok".encode())
                connect_with_succ = sock.recv(1024).decode()
                client.send(connect_with.encode())
                client.recv(1024)
                client.send(connect_with_succ.encode())
                sock.close()

        elif string == "recv_file":
            client.send("ok".encode())
            ext = client.recv(1024).decode()
            client.send("ok".encode())
            fname = client.recv(1024).decode()
            client.send("ok".encode())

            if ext == "txt":
                f = open(str(self.port_nu) + "\\" + fname, "w")
                chunk = client.recv(1024)
                while chunk:
                    f.write((chunk.decode()))
                    chunk = client.recv(1024)
                    if chunk == b"eof":
                        break
                f.close()
            else:
                f = open(str(self.port_nu) + "\\" + fname, "wb")
                chunk = client.recv(1024)
                while chunk:
                    f.write(chunk)
                    chunk = client.recv(1024)
                    if chunk == b"eof":
                        break
                f.close()

        elif string == "send_file":
            client.send("ok".encode())
            file = client.recv(1024).decode()

            ext = file[::-1]
            ind = ext.find(".")
            ext = ext[0:ind]
            ext = ext[::-1]
            pcheck = 0
            try:
                if ext == "txt":
                    f = open(str(self.port_nu) + "\\" + file, "r")
                else:
                    f = open(str(self.port_nu) + "\\" + file, "rb")
                f.close()
                pcheck = 1
            except:
                pcheck = 0

            if pcheck == 0:
                client.send("absent".encode())
                return
            elif pcheck == 1:
                client.send("present".encode())
                client.recv(1024)
                client.send(ext.encode())
                client.recv(1024)

            if ext == "txt":
                with open(file, "r") as f:
                    data = f.read(1024)
                    while data:
                        client.send((data.encode()))
                        data = f.read(1024)
            else:
                with open(file, "rb") as f:
                    data = f.read(1024)
                    while data:
                        client.send(data)
                        data = f.read(1024)
            time.sleep(0.1)
            client.send(b"eof")

        elif string == "make_tables":
            client.send("ok".encode())
            counter = int(client.recv(1024).decode())
            counter = counter - 1
            if counter == 0:
                client.send(str(self.port_nu).encode())
            else:
                sock.connect((ip, int(self.succ_port)))
                sock.send("make_tables".encode())
                sock.recv(1024)
                sock.send(str(counter).encode())
                val = sock.recv(1024).decode()
                client.send(val.encode())
                sock.close()
            client.close()

        elif string == "update_table":
            client.send("ok".encode())
            start = client.recv(1024).decode()
            if str(start) != str(self.port_nu):
                self.make_finger_tables()
                sock = socket.socket()
                sock.connect((ip, int(self.succ_port)))
                sock.send("update_table".encode())
                sock.recv(1024)
                sock.send(str(start).encode())
                sock.close()

        elif string == "get_files":
            client.send("ok".encode())
            files = os.listdir(str(self.port_nu))
            pred_hash = self.hash_function(self.pred_port)
            for file in files:
                # print(file)
                sock = socket.socket()
                ext = file[::-1]
                ind = ext.find(".")
                ext = ext[0:ind]
                ext = ext[::-1]

                file_hash = self.hash_function(file)
                if (
                    (pred_hash >= file_hash and pred_hash < self.hash_val)
                    or (
                        pred_hash < file_hash
                        and pred_hash < self.hash_val
                        and file_hash > self.hash_val
                    )
                    or (pred_hash < self.hash_val and file_hash < pred_hash)
                ):
                    sock.connect((ip, int(self.pred_port)))
                    sock.send("recv_file".encode())
                    sock.recv(1024)
                    sock.send(ext.encode())
                    sock.recv(1024)
                    sock.send(file.encode())
                    sock.recv(1024)

                    if ext == "txt":
                        with open(str(self.port_nu) + "\\" + file, "r") as f:
                            data = f.read(1024)
                            while data:
                                sock.send((data.encode()))
                                data = f.read(1024)
                    else:
                        with open(str(self.port_nu) + "\\" + file, "rb") as f:
                            data = f.read(1024)
                            while data:
                                sock.send(data)
                                data = f.read(1024)
                    time.sleep(0.1)
                    sock.send(b"eof")
                    sock.close()

        client.close()

    def client(self):
        while 1:
            a = input(
                "1. Upload File \n2. Download File \n3. Leave P2P network\n4. Pred/Succ Status\n=> "
            )
            if a == "1":
                if self.succ_port == self.port_nu:
                    print("You are the Only Peer; waiting for connections ...")
                else:
                    print(
                        "==========================================================================================="
                    )
                    while 1:
                        try:
                            file = input("Enter File Directory: ")
                            ext = file[::-1]
                            ind = ext.find(".")
                            ext = ext[0:ind]
                            ext = ext[::-1]
                            if ext == "txt":
                                f = open(file, "r")
                            else:
                                f = open(file, "rb")
                            f.close()
                            break
                        except:
                            print("Invalid File")

                    file_hash = self.hash_function(file)
                    print("File Hash: " + str(file_hash))

                    sock = socket.socket()
                    sock.connect((ip, int(self.succ_port)))
                    sock.send(("find_file").encode())
                    sock.recv(1024)
                    sock.send((str(file_hash).encode()))
                    sock.recv(1024)
                    sock.send(str(self.port_nu).encode())
                    connect_with = sock.recv(1024).decode()
                    sock.send("ok".encode())
                    connect_with_succ = sock.recv(1024).decode()
                    sock.close()

                    file = file[::-1]
                    ind = file.find("\\")
                    if ind != -1:
                        filename = file[0:ind]
                        filename = filename[::-1]
                    else:
                        filename = file[::-1]
                    file = file[::-1]

                    sock = socket.socket()
                    sock.connect((ip, int(connect_with)))
                    sock.send("recv_file".encode())
                    sock.recv(1024)
                    sock.send(ext.encode())
                    sock.recv(1024)
                    sock.send(filename.encode())
                    sock.recv(1024)
                    if ext == "txt":
                        with open(file, "r") as f:
                            data = f.read(1024)
                            while data:
                                sock.send((data.encode()))
                                data = f.read(1024)
                    else:
                        with open(file, "rb") as f:
                            data = f.read(1024)
                            while data:
                                sock.send(data)
                                data = f.read(1024)
                    time.sleep(0.1)
                    sock.send(b"eof")

                    sock = socket.socket()
                    sock.connect((ip, int(connect_with_succ)))
                    sock.send("recv_file".encode())
                    sock.recv(1024)
                    sock.send(ext.encode())
                    sock.recv(1024)
                    sock.send(filename.encode())
                    sock.recv(1024)
                    if ext == "txt":
                        with open(file, "r") as f:
                            data = f.read(1024)
                            while data:
                                sock.send((data.encode()))
                                data = f.read(1024)
                    else:
                        with open(file, "rb") as f:
                            data = f.read(1024)
                            while data:
                                sock.send(data)
                                data = f.read(1024)
                    time.sleep(0.1)
                    sock.send(b"eof")

                    print("File is now on Network")

            elif a == "2":
                if self.succ_port == self.port_nu:
                    print("You are the Only Peer; waiting for connections ...")
                else:
                    print(
                        "==========================================================================================="
                    )
                    file = input("Enter file name: ")
                    file_hash = self.hash_function(file)
                    print("File Hash: " + str(file_hash))

                    sock = socket.socket()
                    sock.connect((ip, int(self.succ_port)))
                    sock.send(("find_file").encode())
                    sock.recv(1024)
                    sock.send((str(file_hash).encode()))
                    sock.recv(1024)
                    sock.send(str(self.port_nu).encode())
                    connect_with = sock.recv(1024).decode()
                    sock.send("ok".encode())
                    connect_with_succ = sock.recv(1024).decode()
                    sock.close()

                    sock = socket.socket()
                    sock.connect((ip, int(connect_with)))
                    sock.send(("send_file").encode())
                    sock.recv(1024)
                    sock.send((str(file).encode()))
                    check = sock.recv(1024).decode()

                    if check == "absent":
                        print("File is not available on the Network")
                    elif check == "present":
                        sock.send("ok".encode())
                        ext = sock.recv(1024).decode()
                        sock.send("ok".encode())
                        if ext == "txt":
                            f = open(str(self.port_nu) + "\\" + file, "w")
                            chunk = sock.recv(1024)
                            while chunk:
                                f.write((chunk.decode()))
                                chunk = sock.recv(1024)
                                if chunk == b"eof":
                                    break
                            f.close()
                        else:
                            f = open(str(self.port_nu) + "\\" + file, "wb")
                            chunk = sock.recv(1024)
                            while chunk:
                                f.write(chunk)
                                chunk = sock.recv(1024)
                                if chunk == b"eof":
                                    break
                            f.close()
                        print("Downloaded")

                    sock.close()

            elif a == "3":
                exit()

            elif a == "4":
                print(
                    "==========================================================================================="
                )
                print(
                    "Pred -> "
                    + str(self.pred_port)
                    + " "
                    + str(self.hash_function(self.pred_port))
                )
                print(
                    "Mine -> "
                    + str(self.port_nu)
                    + " "
                    + str(self.hash_function(self.port_nu))
                )
                print(
                    "Succ -> "
                    + str(self.succ_port)
                    + " "
                    + str(self.hash_function(self.succ_port))
                )
                print("Finger Table:")
                print(self.finger_table)

            else:
                print("ERROR: Invalid input")
                continue
            print(
                "==========================================================================================="
            )

    def server(self):
        server = socket.socket()
        server.bind((ip, int(self.port_nu)))
        server.listen(10)
        while 1:
            client, addr = server.accept()
            _thread.start_new_thread(self.listen, (client, addr))

    def make_finger_tables(self):
        for i in range(0, 5):
            sock = socket.socket()
            sock.connect((ip, int(self.succ_port)))
            sock.send("make_tables".encode())
            sock.recv(1024)
            sock.send(str(pow(2, i)).encode())
            self.finger_table[i] = sock.recv(1024).decode()
            sock.close()

    def check_succ(self):
        while 1:
            time.sleep(0.5)
            sock = socket.socket()
            try:
                sock.connect((ip, int(self.succ_port)))
                sock.close()
            except:
                self.succ_port = self.finger_table[1]
                sock.connect((ip, int(self.succ_port)))
                sock.send("pred_update".encode())
                sock.recv(1024)
                sock.send(str(self.port_nu).encode())
                sock.close()
                self.make_finger_tables()

                sock = socket.socket()
                sock.connect((ip, int(self.succ_port)))
                sock.send("update_table".encode())
                sock.recv(1024)
                sock.send(str(self.port_nu).encode())
                sock.close()

    def __init__(self, port_num):
        server = socket.socket()
        self.port_nu = port_num
        while 1:
            try:
                server.bind((ip, int(self.port_nu)))
                server.close()
                self.hash_val = int(self.hash_function(self.port_nu))
                print("Hash: ", self.hash_val)
                break
            except:
                print("ERROR: Invalid Port (Already Taken or Does not exist)")
                self.port_nu = input("Enter port number: ")

        print(
            "==========================================================================================="
        )
        while 1:
            a = input("1.Join network.\n2.Create new network\n=> ")
            if a == "1":
                print(
                    "==========================================================================================="
                )
                port = input("Enter port number: ")
                self.join(port)
                break
            elif a == "2":
                print(
                    "==========================================================================================="
                )
                print("Network created ... ")
                self.succ_port = self.port_nu
                self.pred_port = self.port_nu
                break
            else:
                print("Invalid Input; Enter 1 or 2.")

        _thread.start_new_thread(self.server, ())

        self.make_finger_tables()

        sock = socket.socket()
        sock.connect((ip, int(self.succ_port)))
        sock.send("get_files".encode())
        sock.recv(1024)
        sock.close()

        sock = socket.socket()
        sock.connect((ip, int(self.succ_port)))
        sock.send("update_table".encode())
        sock.recv(1024)
        sock.send(str(self.port_nu).encode())
        sock.close()

        _thread.start_new_thread(self.check_succ, ())

        self.client()


def Main():
    a = input("Enter Port Number: ")
    b = node(a)


if __name__ == "__main__":
    Main()
