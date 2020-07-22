import 'dart:convert';

class LoginRequestModel {
  final String phone;
  final String password;
  LoginRequestModel({
    this.phone,
    this.password,
  });

  LoginRequestModel copyWith({
    String phone,
    String password,
  }) {
    return LoginRequestModel(
      phone: phone ?? this.phone,
      password: password ?? this.password,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'phone': phone,
      'password': password,
    };
  }

  static LoginRequestModel fromMap(Map<String, dynamic> map) {
    if (map == null) return null;

    return LoginRequestModel(
      phone: map['phone'],
      password: map['password'],
    );
  }

  String toJson() => json.encode(toMap());

  static LoginRequestModel fromJson(String source) =>
      fromMap(json.decode(source));

  @override
  String toString() => 'LoginRequestModel(phone: $phone, password: $password)';
}
