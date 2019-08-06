/usr/libexec/qemu-kvm   \
    -name  'guest-rhel8.0'    \
    -machine  q35   \
    -nodefaults   \
    -vga  qxl \
    -object iothread,id=iothread0 \
    -blockdev driver=qcow2,file.driver=file,cache.direct=off,cache.no-flush=on,file.filename=/home/images/os4.qcow2,node-name=os_image \
    -device pcie-root-port,id=pcie.0-root-port-5,slot=5,chassis=5,bus=pcie.0 \
    -device virtio-blk-pci,id=os,drive=os_image,bus=pcie.0-root-port-5,addr=0x0,werror=stop,rerror=stop,iothread=iothread0,bootindex=0 \
    -vnc :4 \
    -monitor  stdio \
    -m  8192 \
    -smp  8 \
    -device virtio-net-pci,mac=9a:b5:b6:a1:b2:c4,id=idMmq1jH,vectors=4,netdev=idxgXAlm,bus=pcie.0,addr=0x9      \
    -netdev tap,id=idxgXAlm,vhost=on \
    -qmp tcp:localhost:5954,server,nowait  \
    -chardev file,path=/home/serial.log,id=serial_id_serial0 \
    -device isa-serial,chardev=serial_id_serial0  \
    -blockdev node-name=file_cd1,driver=file,read-only=on,filename=/mnt/linux/RHEL-8.1.0-20190701.0-x86_64-dvd1.iso,cache.direct=on,cache.no-flush=off \
    -blockdev node-name=drive_cd1,driver=raw,read-only=on,cache.direct=on,cache.no-flush=off,file=file_cd1 \
    -device ide-cd,id=cd1,drive=drive_cd1,write-cache=on,bus=ide.0,unit=0 \
 \
-device virtio-scsi-pci,id=scsi0 \
\
-object throttle-group,id=foo1_grp,x-iops-total=100 \
-object throttle-group,id=foo2_grp,x-iops-total=200 \
\
    -device pcie-root-port,id=pcie.0-root-port-6,slot=6 \
    -device pcie-root-port,id=pcie.0-root-port-7,slot=7 \
    -device pcie-root-port,id=pcie.0-root-port-8,slot=8 \
    -device pcie-root-port,id=pcie.0-root-port-9,slot=9 \
-blockdev driver=file,cache.direct=on,cache.no-flush=off,filename=/home/images/data4-1.qcow2,node-name=protocol_node1 \
-blockdev driver=qcow2,node-name=format_node1,file=protocol_node1 \
-blockdev driver=throttle,throttle-group=foo1_grp,node-name=filter_node1,file=format_node1 \
-device virtio-blk-pci,bus=pcie.0-root-port-6,drive=filter_node1,id=data1 \
\
-blockdev driver=file,cache.direct=on,cache.no-flush=off,filename=/home/images/data4-2.qcow2,node-name=protocol_node2 \
-blockdev driver=qcow2,node-name=format_node2,file=protocol_node2 \
-device virtio-blk-pci,bus=pcie.0-root-port-7,drive=format_node2,id=data2 \
\
-blockdev driver=file,cache.direct=on,cache.no-flush=off,filename=/home/images/data4-3.qcow2,node-name=protocol_node3 \
-blockdev driver=qcow2,node-name=format_node3,file=protocol_node3 \
-blockdev driver=throttle,throttle-group=foo2_grp,node-name=filter_node3,file=format_node3 \
-device virtio-blk-pci,bus=pcie.0-root-port-8,drive=filter_node3,id=data3 \
\
-blockdev driver=file,cache.direct=on,cache.no-flush=off,filename=/home/images/data4-4.qcow2,node-name=protocol_node4 \
-blockdev driver=qcow2,node-name=format_node4,file=protocol_node4 \
-blockdev driver=throttle,throttle-group=foo2_grp,node-name=filter_node4,file=format_node4 \
-device virtio-blk-pci,bus=pcie.0-root-port-9,drive=filter_node4,id=data4 \
