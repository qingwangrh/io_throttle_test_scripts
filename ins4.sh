/usr/libexec/qemu-kvm   \
    -name  'guest-rhel8.0'    \
    -machine  q35   \
    -nodefaults   \
    -vga  qxl \
    -object iothread,id=iothread0 \
    -blockdev driver=qcow2,file.driver=file,cache.direct=off,cache.no-flush=on,file.filename=/home/images/os4.qcow2,node-name=drive_image2 \
    -device pcie-root-port,id=pcie.0-root-port-5,slot=5,chassis=5,addr=0x5,bus=pcie.0 \
    -device virtio-blk-pci,id=image2,drive=drive_image2,bus=pcie.0-root-port-5,addr=0x0,werror=stop,rerror=stop,iothread=iothread0 \
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
-blockdev driver=qcow2,file.driver=file,cache.direct=off,cache.no-flush=on,file.filename=/home/images/data4.qcow2,node-name=drive_image3 \
 -device pcie-root-port,id=pcie.0-root-port-6,slot=6,chassis=5,addr=0x6,bus=pcie.0 \
-device virtio-blk-pci,id=image3,drive=drive_image3,bus=pcie.0-root-port-6,addr=0x0,werror=stop,rerror=stop,iothread=iothread0 \
