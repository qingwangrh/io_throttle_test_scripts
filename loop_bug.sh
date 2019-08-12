echo "$#"

if (($#==2));then
i_start=$1
i_end=$2
else
i_start=0
i_end=10
fi
for ((idx=${i_start};idx<${i_end};idx++))
do
sleep 1
rm -rf /home/serial${idx}.log
/usr/libexec/qemu-kvm   \
    -name  "guest-rhel8.0-${idx}"    \
    -machine  pc-i440fx-rhel7.6.0,accel=kvm,usb=off,dump-guest-core=off   \
    -cpu Westmere \
    -m 4096 \
    -realtime mlock=off \
    -uuid dbfc4b9a-74bf-4c21-95c6-0840743fd57${idx} \
    -smbios "type=1,manufacturer=Red Hat,product=RHEV Hypervisor,version=7.7-7.el7,serial=4c4c4544-0047-3210-8053-c4c04f473632,uuid=dbfc4b9a-74bf-4c21-95c6-0840743fd57${idx}" \
    -smp 1,maxcpus=16,sockets=16,cores=1,threads=1 \
    -nodefaults   \
    -vga  qxl \
    -object iothread,id=iothread0 \
    -drive file=/mnt/gluster/rhel810-64-virtio${idx}.qcow2,format=qcow2,if=none,id=drive-ua-1,serial=1,werror=stop,rerror=stop,cache=none,aio=native \
    -device virtio-blk-pci,scsi=off,bus=pci.0,addr=0x5,drive=drive-ua-1,id=ua-1,bootindex=1,write-cache=on \
    -vnc :${idx} \
    -monitor  stdio \
    -device virtio-net-pci,mac=9a:b5:b6:a1:b2:c${idx},id=idMmq1jH,vectors=4,netdev=idxgXAlm,bus=pci.0,addr=0x9      \
    -netdev tap,id=idxgXAlm,vhost=on \
    -qmp tcp:localhost:595${idx},server,nowait  \
    -chardev file,path=/home/serial${idx}.log,id=serial_id_serial0 \
    -device isa-serial,chardev=serial_id_serial0  \
    -device vmcoreinfo \
&
done
