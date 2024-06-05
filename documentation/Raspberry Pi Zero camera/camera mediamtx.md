https://www.youtube.com/watch?v=kfHVxvMZMnw

https://phazertech.com/tutorials/rtsp.html

#### Raspberry Pi Cameras

_MediaMTX_ natively supports the Raspberry Pi Camera, enabling high-quality and low-latency video streaming from the camera to any user, for any purpose. There are a couple of requirements:

1. The server must run on a Raspberry Pi, with Raspberry Pi OS bullseye or newer as operative system. Both 32 bit and 64 bit operative systems are supported.

2. Make sure that the legacy camera stack is disabled. Type `sudo raspi-config`, then go to `Interfacing options`, `enable/disable legacy camera support`, choose `no`. Reboot the system.

If you want to run the standard (non-Docker) version of the server:

1. Make sure that the following packages are installed:

   - `libcamera0` (&ge; 0.0.5)
   - `libfreetype6`

2. download the server executable. If you're using 64-bit version of the operative system, make sure to pick the `arm64` variant.

3. edit `mediamtx.yml` and replace everything inside section `paths` with the following content:

   ```yml
   paths:
     cam:
       source: rpiCamera
   ```

The resulting stream will be available in path `/cam`.

### Start on boot

#### Linux

On most Linux distributions (including Ubuntu and Debian, but not OpenWrt), _systemd_ is in charge of managing services and starting them on boot.

Move the server executable and configuration in global folders:

```sh
sudo mv mediamtx /usr/local/bin/
sudo mv mediamtx.yml /usr/local/etc/
```

Create a _systemd_ service:

```sh
sudo tee /etc/systemd/system/mediamtx.service >/dev/null << EOF
[Unit]
Wants=network.target
[Service]
ExecStart=/usr/local/bin/mediamtx /usr/local/etc/mediamtx.yml
[Install]
WantedBy=multi-user.target
EOF
```

Enable and start the service:

```sh
sudo systemctl daemon-reload
sudo systemctl enable mediamtx
sudo systemctl start mediamtx
```

sudo /usr/local/bin/mediamtx &
v4l2-ctl --set-ctrl video_bitrate=10000000 &
ffmpeg -input_format h264 -f video4linux2 -video_size 1640x922 -framerate 15 -i /dev/video0 -c:v copy -an -f rtsp rtsp://localhost:8554/Keuken -rtsp_transport tcp

https://james-batchelor.com/index.php/2023/11/10/install-mediamtx-on-raspbian-bookworm/
