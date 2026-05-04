import 'package:flutter/material.dart';

class PreparationScreen extends StatelessWidget {
  const PreparationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Exam Preparation')),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.checklist, size: 80, color: Colors.teal),
            SizedBox(height: 16),
            Text('Topic-Level Tracking', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            Padding(
              padding: const EdgeInsets.all(24),
              child: Text('Track your progress through units and topics. See your Readiness Score per subject.', textAlign: TextAlign.center),
            ),
          ],
        ),
      ),
    );
  }
}
