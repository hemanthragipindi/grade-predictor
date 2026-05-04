import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../core/api_client.dart';

class AuthProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  final _storage = const FlutterSecureStorage();
  
  bool _isLoading = false;
  Map<String, dynamic>? _user;
  String? _error;

  bool get isLoading => _isLoading;
  Map<String, dynamic>? get user => _user;
  String? get error => _error;

  Future<bool> login(String mobile, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.dio.post('/login', data: {
        'mobile': mobile,
        'password': password,
      });

      if (response.data['success']) {
        final token = response.data['token'];
        await _storage.write(key: 'jwt_token', value: token);
        _user = response.data['user'];
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = response.data['message'] ?? 'Authentication failed';
      }
    } catch (e) {
      _error = 'Connection error. Please try again.';
    }

    _isLoading = false;
    notifyListeners();
    return false;
  }

  Future<bool> register(String name, String email, String mobile, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.dio.post('/register', data: {
        'name': name,
        'email': email,
        'mobile': mobile,
        'password': password,
      });

      if (response.data['success']) {
        final token = response.data['token'];
        await _storage.write(key: 'jwt_token', value: token);
        _user = response.data['user'];
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = response.data['message'] ?? 'Registration failed';
      }
    } catch (e) {
      _error = 'Connection error. Please try again.';
    }

    _isLoading = false;
    notifyListeners();
    return false;
  }

  Future<void> logout() async {
    await _storage.delete(key: 'jwt_token');
    _user = null;
    notifyListeners();
  }

  Future<void> checkStatus() async {
    final token = await _storage.read(key: 'jwt_token');
    if (token != null) {
      try {
        final response = await _api.dio.get('/dashboard');
        if (response.statusCode == 200) {
          _user = response.data['user'];
        }
      } catch (e) {
        await logout();
      }
    }
    notifyListeners();
  }
}
