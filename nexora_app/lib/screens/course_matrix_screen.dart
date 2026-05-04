import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class CourseMatrixScreen extends StatelessWidget {
  const CourseMatrixScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;
    final subjects = user?['subjects'] as List? ?? [];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Course Matrix'),
        backgroundColor: Colors.blue.shade900,
        foregroundColor: Colors.white,
      ),
      body: Container(
        color: Colors.grey.shade50,
        child: subjects.isEmpty 
          ? _buildEmptyState()
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: subjects.length,
              itemBuilder: (context, index) {
                final subject = subjects[index];
                return _buildSubjectCard(context, subject);
              },
            ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.auto_stories, size: 80, color: Colors.grey),
          SizedBox(height: 16),
          Text('No courses found.', style: TextStyle(fontSize: 18, color: Colors.grey)),
          Text('Add subjects on the web to see them here.', style: TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }

  Widget _buildSubjectCard(BuildContext context, dynamic subject) {
    final double risk = double.tryParse(subject['failure_risk']?.toString() ?? '0') ?? 0;
    final String priority = subject['priority'] ?? 'Medium';
    final Color riskColor = risk > 70 ? Colors.red : (risk > 30 ? Colors.orange : Colors.green);

    return Card(
      elevation: 4,
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        subject['subject_code'] ?? 'CODE',
                        style: TextStyle(color: Colors.blue.shade800, fontWeight: FontWeight.bold),
                      ),
                      Text(
                        subject['subject_name'] ?? 'Subject Name',
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: riskColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: riskColor),
                  ),
                  child: Text(
                    'Risk: ${risk.toStringAsFixed(0)}%',
                    style: TextStyle(color: riskColor, fontWeight: FontWeight.bold, fontSize: 12),
                  ),
                ),
              ],
            ),
            const Divider(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildInfoColumn('Credits', '${subject['credits'] ?? '0'}', Icons.layers),
                _buildInfoColumn('Priority', priority, Icons.priority_high, 
                  color: priority == 'High' ? Colors.red : Colors.blue),
                _buildInfoColumn('Target', '${subject['target_grade'] ?? 'A'}', Icons.track_changes),
              ],
            ),
            const SizedBox(height: 20),
            _buildImpactBar(subject['gpa_sensitivity'] ?? 0.5),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoColumn(String label, String value, IconData icon, {Color? color}) {
    return Column(
      children: [
        Icon(icon, size: 20, color: Colors.grey),
        const SizedBox(height: 4),
        Text(value, style: TextStyle(fontWeight: FontWeight.bold, color: color)),
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.grey)),
      ],
    );
  }

  Widget _buildImpactBar(dynamic sensitivity) {
    final double val = double.tryParse(sensitivity.toString()) ?? 0.5;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('GPA Impact Sensitivity', style: TextStyle(fontSize: 12, color: Colors.grey)),
            Text('${(val * 100).toStringAsFixed(0)}%', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
          ],
        ),
        const SizedBox(height: 6),
        LinearProgressIndicator(
          value: val,
          backgroundColor: Colors.grey.shade200,
          valueColor: AlwaysStoppedAnimation<Color>(Colors.blue.shade700),
          minHeight: 6,
          borderRadius: BorderRadius.circular(3),
        ),
      ],
    );
  }
}
