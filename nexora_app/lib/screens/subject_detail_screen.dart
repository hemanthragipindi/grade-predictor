import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../core/api_client.dart';

class SubjectDetailScreen extends StatefulWidget {
  final Map<String, dynamic> subject;

  const SubjectDetailScreen({super.key, required this.subject});

  @override
  State<SubjectDetailScreen> createState() => _SubjectDetailScreenState();
}

class _SubjectDetailScreenState extends State<SubjectDetailScreen> {
  bool _isEditing = false;
  late TextEditingController _caController;
  late TextEditingController _midController;
  late TextEditingController _endController;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _caController = TextEditingController(text: widget.subject['ca_marks']?.toString() ?? '0');
    _midController = TextEditingController(text: widget.subject['mid_marks']?.toString() ?? '0');
    _endController = TextEditingController(text: widget.subject['end_marks']?.toString() ?? '0');
  }

  Future<void> _saveMarks() async {
    setState(() => _isLoading = true);
    try {
      final api = ApiClient();
      final response = await api.dio.post('/subjects/${widget.subject['id']}/marks', data: {
        'ca_marks': _caController.text,
        'mid_marks': _midController.text,
        'end_marks': _endController.text,
      });

      if (response.data['success']) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Marks Saved Successfully!'), backgroundColor: Colors.green),
          );
          setState(() => _isEditing = false);
          // Refresh user data to update dashboard
          await context.read<AuthProvider>().checkStatus();
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to save marks.'), backgroundColor: Colors.red),
        );
      }
    }
    setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.subject['subject_code'] ?? 'Subject Details'),
        actions: [
          IconButton(
            icon: Icon(_isEditing ? Icons.close : Icons.edit),
            onPressed: () => setState(() => _isEditing = !_isEditing),
          )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.subject['subject_name'] ?? 'Subject Name',
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 32),
            _buildMarkInput('Continuous Assessment (CA)', _caController, _isEditing),
            const SizedBox(height: 16),
            _buildMarkInput('Mid-Term (Objective)', _midController, _isEditing),
            const SizedBox(height: 16),
            _buildMarkInput('End-Term (Theory/Practical)', _endController, _isEditing),
            const SizedBox(height: 40),
            if (_isEditing)
              SizedBox(
                width: double.infinity,
                height: 55,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _saveMarks,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue.shade900,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  child: _isLoading 
                    ? const CircularProgressIndicator(color: Colors.white) 
                    : const Text('Save Changes', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildMarkInput(String label, TextEditingController controller, bool enabled) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: Colors.grey, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          enabled: enabled,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(
            filled: !enabled,
            fillColor: Colors.grey.shade100,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
      ],
    );
  }
}
