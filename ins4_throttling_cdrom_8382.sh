/usr/libexec/qemu-kvm   \
    -name  'guest-rhel8.0'    \
    -machine  q35   \
    -nodefaults   \
    -vga  qxl \
    -object iothread,id=iothread0 \
    -blockdev driver=qcow2,file.driver=file,cache.direct=off,cache.no-flush=on,file.filename=/home/images/os4.qcow2,node-name=drive_image2 \
    -device pcie-root-port,id=pcie.0-root-port-5,slot=5,chassis=5,addr=0x5,bus=pcie.0 \
    -device virtio-blk-pci,id=image2,drive=drive_image2,bus=pcie.0-root-port-5,addr=0x0,werror=stop,rerror=stop,iothread=iothread0,bootindex=0 \
    -vnc :4 \
    -monitor  stdio \
    -m  8192 \
    -smp  8 \
    -device virtio-net-pci,mac=9a:b5:b6:a1:b2:c4,id=idMmq1jH,vectors=4,netdev=idxgXAlm,bus=pcie.0,addr=0x9      \
    -netdev tap,id=idxgXAlm,vhost=on \
    -qmp tcp:localhost:5954,server,nowait  \
    -chardev file,path=/home/serial.log,id=serial_id_serial0 \
    -device isa-serial,chardev=serial_id_serial0  \
 \
-object throttle-group,id=foo,x-bps-total=409600 \
-blockdev driver=file,cache.direct=on,cache.no-flush=off,filename=/home/images/data4.qcow2,node-name=file_stg1 \
-blockdev driver=qcow2,node-name=drive_stg1,file=file_stg1 \
-blockdev driver=throttle,throttle-group=foo,node-name=foo1,file=drive_stg1 \
-device pcie-root-port,id=pcie.0-root-port-6,slot=6,chassis=5,addr=0x6,bus=pcie.0 \
-device virtio-blk-pci,drive=foo1,id=data,bus=pcie.0-root-port-6,addr=0x0 \
 \
-device virtio-scsi-pci,id=scsi0 \
-drive file=/home/images/data4.raw,if=none,id=drive-scsi0-0-1-0,format=raw,cache=none,bps=30720000,iops=100,throttling.group=scsi,iops_size=4096 \
-device scsi-hd,bus=scsi0.0,channel=0,scsi-id=1,lun=0,drive=drive-scsi0-0-1-0,id=scsi0-0-1-0 \
-drive file=/home/images/cd1.iso,if=none,id=drive-scsi0-0-1-2,readonly=on,format=raw,cache=none,bps=1024000,iops=150,throttling.group=cdrom \
-device scsi-cd,bus=scsi0.0,channel=0,scsi-id=1,lun=1,drive=drive-scsi0-0-1-2,id=cd1 \
\
-object throttle-group,id=cdrom2,x-bps-total=1024000,x-iops-total=100 \
-blockdev driver=throttle,throttle-group=cdrom2,cache.direct=off,cache.no-flush=on,file.filename=/home/images/cd1.iso,node-name=cdrom2,file.driver=file,read-only=on \
-device scsi-cd,drive=cdrom2,id=cd2 \
