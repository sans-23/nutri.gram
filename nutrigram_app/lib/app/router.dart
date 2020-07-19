import 'package:auto_route/auto_route_annotations.dart';
import 'package:nutrigram_app/ui/views/auth/login/login_view.dart';
import 'package:nutrigram_app/ui/views/auth/register/register_view.dart';
import 'package:nutrigram_app/ui/views/startup/startup_view.dart';

@MaterialAutoRouter(routes: [
  MaterialRoute(page: StartUpView, initial: true),
  MaterialRoute(page: LoginView),
  MaterialRoute(page: RegisterView)
])
class $Router {}