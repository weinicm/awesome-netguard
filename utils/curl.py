import asyncio
import subprocess
import os
import re
import logging
from urllib.parse import urlparse
import uuid

class CurlRunner:
    @staticmethod
    async def run(ip, download_url, port, timeout):
        logging.info("Downloading file with curl")
        # 生成唯一的文件名
        unique_id = f"{int(asyncio.get_event_loop().time())}_{uuid.uuid4().hex[:6]}"
        output_file = f'downloaded_file_{unique_id}.zip'

        # 解析 URL 获取主机名
        parsed_url = urlparse(download_url)
        hostname = parsed_url.hostname

        # 构建 curl 命令
        curl_command = [
            'curl',
            '--resolve', f'{hostname}:{port}:{ip}',  # 将域名解析到指定的 IP 和端口
            '--output', output_file,  # 输出文件
            '--show-error',  # 显示错误信息
            '--max-time', str(timeout),  # 设置超时时间
            download_url
        ]
        logging.info(f"Running curl command: {' '.join(curl_command)}")

        # 记录开始时间
        start_time = asyncio.get_event_loop().time()
        last_output_time = start_time  # 初始化最后输出时间

        # 运行 curl 命令
        process = await asyncio.create_subprocess_exec(
            *curl_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            while True:
                # 等待一段时间
                await asyncio.sleep(1)

                # 检查是否超时
                if (asyncio.get_event_loop().time() - start_time) > timeout:
                    logging.info("Download timed out, stopping the download.")
                    process.terminate()  # 终止进程
                    break

                # 检查是否有新的输出
                if (asyncio.get_event_loop().time() - last_output_time) > 30:  # 如果 30 秒内没有新的输出
                    logging.info("No new output for 30 seconds, assuming the download is unresponsive, stopping the download.")
                    process.terminate()  # 终止进程
                    break

                # 读取并过滤 stderr 输出
                stderr_line = await process.stderr.readline()
                if not stderr_line:
                    continue
                stderr_line = stderr_line.decode().strip()

                # 过滤掉特定的 TLS 日志信息
                if not re.match(r'^\* TLSv1\.2 $IN$, TLS header, Supplemental data $23$:', stderr_line):
                    logging.info(stderr_line)
                    last_output_time = asyncio.get_event_loop().time()  # 更新最后输出时间
        except asyncio.CancelledError:
            # 如果下载被取消，则终止进程
            process.terminate()
            raise
        finally:
            # 确保进程完全终止
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                logging.warning("Process did not terminate in time, forcing termination.")
                process.kill()

            # 等待进程完成并获取输出
            stdout, stderr = await process.communicate()

            # 检查是否成功下载了文件
            if not os.path.exists(output_file):
                logging.error("Download failed. The file was not found.")
                return None
            else:
                # 获取文件大小（字节）
                file_size_bytes = os.path.getsize(output_file)

                # 如果文件大小为0，返回None
                if file_size_bytes == 0:
                    logging.error("Downloaded file size is 0, returning None.")
                    os.remove(output_file)
                    return None

                # 计算平均下载速度（单位：MB/s）
                average_speed_mbps = round((file_size_bytes / 1024 / 1024) / timeout, 2)

                # 打印平均下载速度
                logging.info(f"Download completed. Total time: {timeout:.2f}s, Downloaded size: {file_size_bytes} bytes")
                logging.info(f"Average download speed: {average_speed_mbps:.2f} MB/s")

                # 删除下载的文件
                os.remove(output_file)
                logging.info(f"Downloaded file '{output_file}' has been deleted.")
                speed = average_speed_mbps
                return ip,speed