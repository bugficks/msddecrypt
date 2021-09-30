# msddecrypt
Samsung TV Tizen firmware/msd file decryptor

Build docker image:  
```
docker-compose build  
```
  
Run msddecrypt:
```
#️  docker-compose run --rm msddecrypt

Tizen msd Decryptor v0.5.0
(c) bugficks@samygo 2016-2021

Usage: msddecrypt.py </path/to/upgrade.msd> [/path/to/outdir [partition names]]
```

```
#️  docker-compose run --rm msddecrypt images/T-KTSDEUC_1210.8/image/upgrade.msd out uImage

Tizen msd Decryptor v0.5.0
(c) bugficks@samygo 2016-2021

magic: MSDU11
headers [12]
T-KTSAKUC   : offs: 000001ca size: 00000e08
T-KTSDEUC   : offs: 00000fd2 size: 00000e08
T-KTSUABC   : offs: 00001dda size: 00000e08
T-KTSDCNC   : offs: 00002be2 size: 00000e08
T-KTSNAKUC  : offs: 000039ea size: 00000e08
T-KTSNDEUC  : offs: 000047f2 size: 00000e08
T-KTSNUABC  : offs: 000055fa size: 00000e08
T-KTSNDCNC  : offs: 00006402 size: 00000e08
T-KTSUAKUC  : offs: 0000720a size: 00000e08
T-KTSUDEUC  : offs: 00008012 size: 00000e08
T-KTSUUABC  : offs: 00008e1a size: 00000e08
T-KTSUDCNC  : offs: 00009c22 size: 00000e08

Found valid header magic
T-KTSAKUC 39332605ff47a0aea999b10ce9087389 0x00000106
image ver: T-KTSDEUC 1210.8

partitions [8]
id: 1 name: secos.bin     salt: ce6a1d0ce5aef20a offs: 0000aa2a size: 001fe010 crc32: 692e44bf
id: 2 name: seret.bin     salt: b65e77f138b2774e offs: 00208a3a size: 001fe010 crc32: 7568b6fc
id: 3 name: uImage        salt: 2c85795b409aa7e5 offs: 00406a4a size: 0061edf0 crc32: 38637f4d
* Decrypting 'out/uImage' 100% [0061edf0 of 0061edf0]
* CRC32ing   'out/uImage' 100%
+ CRC32 passed!
id: 4 name: ddr.init      salt: 966af6f0beb4aa29 offs: 00a2583a size: 0000a010 crc32: d1b334b3
id: 5 name: dtb.bin       salt: da0691c2064511c7 offs: 00a2f84a size: 000fe010 crc32: 29efece6
id: 6 name: platform.img  salt: dac6fb22a634435e offs: 00b2d85a size: 47f7d010 crc32: ecd96e68
id: 7 name: secos_drv.bin salt: 02e96626be6f11f6 offs: 48aaa86a size: 000fe010 crc32: e36d7047
id: 8 name: sign.bin      salt: d8410374210e17b9 offs: 48ba887a size: 00000410 crc32: 1122f29f
```
