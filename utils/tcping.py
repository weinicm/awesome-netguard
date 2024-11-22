import asyncio
from datetime import datetime
import math
import socket

class TcpingRunner:
    @staticmethod
    async def tcp_ping(host, port, timeout=1):
        # 开始计时
        start_time = datetime.now()
        try:
            # 尝试连接到目标主机和端口
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
            
            # 如果连接成功，记录结束时间
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # 关闭连接
            writer.close()
            await writer.wait_closed()
            
            return True, response_time
        except asyncio.TimeoutError:
            # 如果超时，返回失败
            return False, 'Timeout'
        except Exception as e:
            # 捕获其他异常
            return False, str(e)

    @staticmethod
    async def run(host, port, count=10, interval=1, timeout=1):
        results = []
        for i in range(count):
            result, response_time = await TcpingRunner.tcp_ping(host, port, timeout)
            if result:
                print(f"Connection to {host}:{port} successful. Response time: {response_time:.2f} ms")
            else:
                print(f"Connection to {host}:{port} failed. Reason: {response_time}")
            results.append((result, response_time))
            if i < count - 1:
                await asyncio.sleep(interval)
        
        # 打印统计信息
        success_count = sum(1 for r, _ in results if r)
        successful_response_times = [r for _, r in results if r is not None and isinstance(r, (int, float))]
        
        if success_count > 0:
            avg_latency, std_deviation = TcpingRunner.calculate_stats(successful_response_times)
            packet_loss = (count - success_count) / count 
            print(f"\n--- {host}:{port} tcping statistics ---")
            print(f"{count} packets transmitted, {success_count} packets received, {packet_loss:.2f}% packet loss")
            print(f"round-trip min/avg/max = {min(successful_response_times):.2f}/{avg_latency:.2f}/{max(successful_response_times):.2f} ms")
            print(f"Standard Deviation: {std_deviation:.4f} ms")

    @staticmethod
    async def run_with_stats(host, port, count=10, interval=1, timeout=1):
        results = []
        for i in range(count):
            result, response_time = await TcpingRunner.tcp_ping(host, port, timeout)
            if result:
                print(f"Connection to {host}:{port} successful. Response time: {response_time:.2f} ms")
            else:
                print(f"Connection to {host}:{port} failed. Reason: {response_time}")
            results.append((result, response_time))
            if i < count - 1:
                await asyncio.sleep(interval)
        
        # 计算统计信息
        success_count = sum(1 for r, _ in results if r)
        successful_response_times = [r for _, r in results if r is not None and isinstance(r, (int, float))]
        
        if success_count == 0:
            # 如果没有成功的响应，返回 None
            return None
        
        avg_latency, std_deviation = TcpingRunner.calculate_stats(successful_response_times)
        packet_loss = (count - success_count) / count 
        print(f"\n--- {host}:{port} tcping statistics ---")
        print(f"{count} packets transmitted, {success_count} packets received, {packet_loss:.2f}% packet loss")
        print(f"round-trip min/avg/max = {min(successful_response_times):.2f}/{avg_latency:.2f}/{max(successful_response_times):.2f} ms")
        print(f"Standard Deviation: {std_deviation:.4f} ms")

        # 返回结果
        return (
            f"{host}:{port}",
            round(avg_latency, 2),
            round(std_deviation, 4),
            round(packet_loss, 2)
        )

    @staticmethod
    def calculate_stats(response_times):
        n = len(response_times)
        if n == 0:
            return 0.0, 0.0

        # 计算平均延迟
        avg_latency = sum(response_times) / n

        # 计算标准差
        variance = sum((x - avg_latency) ** 2 for x in response_times) / n
        std_deviation = math.sqrt(variance)

        return avg_latency, std_deviation

# 示例用法
if __name__ == "__main__":
    import asyncio

    async def main():
        # 只打印测试信息
        await TcpingRunner.run('2001:db8::1', 80, count=5, interval=1, timeout=1)  # IPv6 地址

        # 打印测试信息并返回统计信息
        stats = await TcpingRunner.run_with_stats('2001:db8::1', 80, count=5, interval=1, timeout=1)  # IPv6 地址
        if stats is None:
            print("\nFinal Result:")
            print("No successful responses. The IP may be unreachable or there are other issues.")
        else:
            print("\nFinal Result:")
            print(f"IP: {stats[0]}")
            print(f"Avg Latency: {stats[1]:.2f} ms")
            print(f"Std Deviation: {stats[2]:.4f} ms")
            print(f"Packet Loss: {stats[3]:.2f}%")

    asyncio.run(main())