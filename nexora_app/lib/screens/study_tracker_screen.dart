import 'package:flutter/material.dart';

class StudyTrackerScreen extends StatelessWidget {
  const StudyTrackerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Study Tracker')),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.calendar_today, size: 80, color: Colors.orange),
            SizedBox(height: 16),
            Text('Timetable & Task Planning', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            Padding(
              padding: const EdgeInsets.all(24),
              child: Text('This module uses your syllabus to generate a custom study plan based on subject priority.', textAlign: TextAlign.center),
            ),
          ],
        ),
      ),
    );
  }
}
