file=/rhev/data-center/mnt/glusterSD/gluster01.lab.eng.tlv2.redhat.com:_GE__7__volume01/92e8d1b3-bc5b-4759-a997-c5cbdb32f6e7/images/802da913-14f2-4124-9380-e17ca889bf35/f6071c14-70ac-487c-a87d-fb7bef7ee45a
mac=00:1a:4a:16:88:4c
idx=8
/usr/libexec/qemu-kvm   \
    -name  "guest-rhel8.0-${idx}"    \
    -machine  pc-i440fx-rhel7.6.0,accel=kvm,usb=off,dump-guest-core=off   \
    -cpu Westmere \
    -m 6144 \
    -realtime mlock=off \
    -uuid dbfc4b9a-74bf-4c21-95c6-0840743fd57a \
    -smbios 'type=1,manufacturer=Red Hat,product=RHEV Hypervisor,version=7.7-7.el7,serial=4c4c4544-0047-3210-8053-c4c04f473632,uuid=dbfc4b9a-74bf-4c21-95c6-0840743fd57a' \
    -smp 1,maxcpus=16,sockets=16,cores=1,threads=1 \
    -nodefaults   \
    -vga  qxl \
    -object iothread,id=iothread0 \
    -drive file=${file},format=qcow2,if=none,id=drive-ua-1,serial=1,werror=stop,rerror=stop,cache=none,aio=native \
    -device virtio-blk-pci,scsi=off,bus=pci.0,addr=0x5,drive=drive-ua-1,id=ua-1,bootindex=1,write-cache=on \
    -vnc :2${idx} \
    -monitor  stdio \
    -device virtio-net-pci,mac=${mac},id=idMmq1jH,vectors=4,netdev=idxgXAlm,bus=pci.0,addr=0x9      \
    -netdev tap,id=idxgXAlm,vhost=on \
    -qmp tcp:localhost:595${idx},server,nowait  \
    -chardev file,path=/home/serial${idx}.log,id=serial_id_serial0 \
    -device isa-serial,chardev=serial_id_serial0  \
    -device vmcoreinfo \
& \
