import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Nexora Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              context.read<AuthProvider>().logout();
              Navigator.pushReplacementNamed(context, '/login');
            },
          )
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.pushNamed(context, '/assistant'),
        backgroundColor: Colors.blue.shade900,
        child: const Icon(Icons.psychology, color: Colors.white),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Welcome, ${user?['name'] ?? 'User'}!',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: Colors.blue.shade900,
              ),
            ),
            const SizedBox(height: 24),
            _buildStatCard(
              context,
              'Academic Standing',
              '${user?['gpa_tier'] ?? 'Standard'}',
              Icons.stars,
              Colors.amber.shade700,
            ),
            const SizedBox(height: 16),
            _buildStatCard(
              context,
              'Current CGPA',
              '${user?['cgpa'] ?? '0.0'}',
              Icons.trending_up,
              Colors.green,
            ),
            const SizedBox(height: 16),
            _buildStatCard(
              context,
              'High Risk Subjects',
              '${user?['high_risk_count'] ?? '0'}',
              Icons.warning_amber_rounded,
              Colors.red,
            ),
            const SizedBox(height: 32),
            const Text(
              'Academic Insights',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            _buildInsightsSection(user?['insights']),
            const SizedBox(height: 32),
            const Text(
              'Quick Actions',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _buildActionItem(context, 'Cloud Vault', Icons.cloud_upload, Colors.blue),
                const SizedBox(width: 16),
                _buildActionItem(context, 'Course Matrix', Icons.table_chart, Colors.purple),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _buildActionItem(context, 'Study Tracker', Icons.calendar_today, Colors.orange),
                const SizedBox(width: 16),
                _buildActionItem(context, 'Preparation', Icons.checklist, Colors.teal),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCard(BuildContext context, String title, String value, IconData icon, Color color) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: color.withOpacity(0.1),
              child: Icon(icon, color: color),
            ),
            const SizedBox(width: 16),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: Colors.grey)),
                Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionItem(BuildContext context, String title, IconData icon, Color color) {
    return Expanded(
      child: InkWell(
        onTap: () {
          if (title == 'Course Matrix') {
            Navigator.pushNamed(context, '/matrix');
          } else if (title == 'Study Tracker') {
            Navigator.pushNamed(context, '/tracker');
          } else if (title == 'Preparation') {
            Navigator.pushNamed(context, '/prep');
          }
        },
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: color.withOpacity(0.3)),
          ),
          child: Column(
            children: [
              Icon(icon, color: color, size: 32),
              const SizedBox(height: 8),
              Text(title, style: TextStyle(color: color, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInsightsSection(dynamic insights) {
    if (insights == null || (insights is List && insights.isEmpty)) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.blue.shade100),
        ),
        child: const Text('Add your subjects to see academic insights!', 
          style: TextStyle(color: Colors.grey, fontStyle: FontStyle.italic)),
      );
    }

    List<dynamic> insightList = insights is List ? insights : [insights.toString()];

    return Column(
      children: insightList.map((insight) => Padding(
        padding: const EdgeInsets.only(bottom: 8.0),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.blue.shade50,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.blue.shade100),
          ),
          child: Row(
            children: [
              const Icon(Icons.lightbulb, color: Colors.amber, size: 20),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  insight.toString(),
                  style: const TextStyle(fontSize: 14, color: Colors.black87),
                ),
              ),
            ],
          ),
        ),
      )).toList(),
    );
  }
}
