from django.shortcuts import render
from django.http import JsonResponse
from .forms import PingForm
from scapy.all import sr1, IP, ICMP
import socket
import speedtest

def ping_view(request):
    server_ip = socket.gethostbyname(socket.gethostname())  # Get the server's IP

    if request.method == 'POST':
        form = PingForm(request.POST)
        if form.is_valid():
            target = form.cleaned_data['target'] or server_ip  # Use server IP if target is empty
            user_ip = get_user_ip(request)  # Get user's IP
            results = send_icmp_echo(server_ip, target, 20, user_ip)  # Pass the user's IP
            speed_test_results = perform_speed_test()
            return JsonResponse({
                'results': results,
                'speed_test_results': speed_test_results,
            })
    else:
        form = PingForm(initial={'target': server_ip})  # Set server IP as default target

    return render(request, 'pingapp/ping.html', {
        'form': form,
        'server_ip': server_ip,  # Pass server IP to the template
    })

def get_user_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]  # Get the first IP in the list
    return request.META.get('REMOTE_ADDR')  # Fallback to REMOTE_ADDR

def send_icmp_echo(server_ip, target, count, user_ip):
    sent_count = 0
    received_count = 0
    latencies = []

    try:
        destination_ip = socket.gethostbyname(target)
    except socket.error:
        destination_ip = "Unable to resolve"

    for i in range(count):
        packet = IP(src=user_ip, dst=destination_ip) / ICMP()  # Set the source IP to the user's IP
        response = sr1(packet, verbose=0)

        sent_count += 1
        if response:
            received_count += 1
            latencies.append((response.time - packet.sent_time) * 1000)

    packet_loss = ((sent_count - received_count) / sent_count) * 100 if sent_count else 100
    average_latency = sum(latencies) / len(latencies) if latencies else None
    jitter = calculate_jitter(latencies) if len(latencies) > 1 else 0

    return {
        'packet_loss': packet_loss,
        'average_ping': average_latency,
        'sent_count': sent_count,
        'received_count': received_count,
        'ping_times': latencies,
        'jitter': jitter,
        'source_ip': user_ip,
        'destination_ip': destination_ip,
    }

def calculate_jitter(latencies):
    if len(latencies) < 2:
        return 0
    jitter_values = [abs(latencies[i] - latencies[i-1]) for i in range(1, len(latencies))]
    return sum(jitter_values) / len(jitter_values)

def perform_speed_test():
    st = speedtest.Speedtest()
    download_speed = st.download() / 1_000_000  
    upload_speed = st.upload() / 1_000_000      
    server_info = st.get_best_server()

    return {
        'download_speed': download_speed,
        'upload_speed': upload_speed,
        'server': server_info['sponsor'],  
        'location': server_info['name'],    
        'latency': server_info['latency'], 
    }
