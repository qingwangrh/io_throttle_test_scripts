

for ((i=2;i<5;i++)) 
do
	let iops=${i}*10
/usr/libexec/qemu-kvm   \
    -name  "guest-rhel8.0-${i}"    \
    -machine  q35   \
    -nodefaults   \
    -vga  qxl \
    -object iothread,id=iothread0 \
    -blockdev driver=qcow2,file.driver=file,cache.direct=off,cache.no-flush=on,file.filename=/home/images/os${i}.qcow2,node-name=drive_image2 \
    -device pcie-root-port,id=pcie.0-root-port-5,slot=5 \
    -device virtio-blk-pci,id=image2,drive=drive_image2,bus=pcie.0-root-port-5,addr=0x0,werror=stop,rerror=stop,iothread=iothread0,bootindex=1 \
    -vnc :${i} \
    -monitor  stdio \
    -m  8192 \
    -smp  8 \
    -device virtio-net-pci,mac=9a:b5:b6:a1:b2:c${i},id=idMmq1jH,vectors=4,netdev=idxgXAlm,bus=pcie.0,addr=0x9      \
    -netdev tap,id=idxgXAlm,vhost=on \
    -qmp tcp:localhost:595${i},server,nowait  \
    -chardev file,path=/home/serial${i}.log,id=serial_id_serial0 \
    -device isa-serial,chardev=serial_id_serial0  \
    -blockdev node-name=file_cd1,driver=file,read-only=on,filename=/mnt/linux/RHEL-8.1.0-20190701.0-x86_64-dvd1.iso,cache.direct=on,cache.no-flush=off \
    -blockdev node-name=drive_cd1,driver=raw,read-only=on,cache.direct=on,cache.no-flush=off,file=file_cd1 \
    -device ide-cd,id=cd1,drive=drive_cd1,write-cache=on,bus=ide.0,unit=0 \
\
-device virtio-scsi-pci,id=scsi0 \
\
-object throttle-group,id=foo1_grp,x-iops-total=${iops} \
\
-device pcie-root-port,id=pcie.0-root-port-6,slot=6 \
-blockdev driver=file,cache.direct=on,cache.no-flush=off,filename=/home/images/data${i}-1.qcow2,node-name=protocol_node1 \
-blockdev driver=qcow2,node-name=format_node1,file=protocol_node1 \
-blockdev driver=throttle,throttle-group=foo1_grp,node-name=filter_node1,file=format_node1 \
-device virtio-blk-pci,bus=pcie.0-root-port-6,drive=filter_node1,id=data1 \
&
done
