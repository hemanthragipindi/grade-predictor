import 'dart:io';
import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';
import 'package:open_file_plus/open_file_plus.dart';
import 'package:permission_handler/permission_handler.dart';

class UpdateScreen extends StatefulWidget {
  final String apkUrl;
  final String newVersion;

  const UpdateScreen({super.key, required this.apkUrl, required this.newVersion});

  @override
  State<UpdateScreen> createState() => _UpdateScreenState();
}

class _UpdateScreenState extends State<UpdateScreen> {
  double progress = 0;
  String speed = "0 KB/s";
  bool downloading = false;
  String? error;

  Future<void> downloadAndInstall() async {
    // Request storage and install permissions
    if (await Permission.requestInstallPackages.request().isGranted) {
      setState(() {
        downloading = true;
        error = null;
      });

      try {
        final dir = await getExternalStorageDirectory();
        final path = "${dir!.path}/nexora_v${widget.newVersion}.apk";
        
        final startTime = DateTime.now();

        await Dio().download(
          widget.apkUrl,
          path,
          onReceiveProgress: (received, total) {
            if (total != -1) {
              final percent = received / total;
              final elapsed = DateTime.now().difference(startTime).inSeconds + 1;
              final kbps = (received / 1024) / elapsed;

              setState(() {
                progress = percent;
                speed = kbps > 1024 
                  ? "${(kbps / 1024).toStringAsFixed(1)} MB/s" 
                  : "${kbps.toStringAsFixed(1)} KB/s";
              });
            }
          },
        );

        setState(() => downloading = false);
        await OpenFile.open(path);
      } catch (e) {
        setState(() {
          downloading = false;
          error = "Download failed. Please check your internet.";
        });
      }
    } else {
      setState(() {
        error = "Install permission is required to update.";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        padding: const EdgeInsets.all(32),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Colors.blue.shade900, Colors.blue.shade800],
          ),
        ),
        child: Center(
          child: Card(
            elevation: 16,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.system_update, size: 80, color: Colors.blue),
                  const SizedBox(height: 24),
                  const Text(
                    "Update Required",
                    style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Version ${widget.newVersion} is available",
                    style: TextStyle(color: Colors.grey.shade600, fontSize: 16),
                  ),
                  const SizedBox(height: 32),
                  if (downloading) ...[
                    LinearProgressIndicator(
                      value: progress,
                      backgroundColor: Colors.grey.shade200,
                      valueColor: const AlwaysStoppedAnimation<Color>(Colors.blue),
                      minHeight: 10,
                      borderRadius: BorderRadius.circular(5),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text("${(progress * 100).toStringAsFixed(0)}%", 
                          style: const TextStyle(fontWeight: FontWeight.bold)),
                        Text(speed, style: TextStyle(color: Colors.grey.shade600)),
                      ],
                    ),
                  ] else ...[
                    if (error != null)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 16),
                        child: Text(error!, style: const TextStyle(color: Colors.red)),
                      ),
                    SizedBox(
                      width: double.infinity,
                      height: 55,
                      child: ElevatedButton.icon(
                        onPressed: downloadAndInstall,
                        icon: const Icon(Icons.download),
                        label: const Text("Update Now", style: TextStyle(fontSize: 18)),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue.shade700,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
