package controllers

import javax.inject._
import play.api.mvc._
import play.api.data._
import play.api.data.Forms._
import models.UsuarioRepository
import scala.concurrent.{ExecutionContext, Future}
import at.favre.lib.crypto.bcrypt.BCrypt

// LoginForm fuera de la clase para que la vista lo referencie sin ambiguedad
case class LoginForm(alias: String, password: String)

@Singleton
class AuthController @Inject()(
  val controllerComponents: ControllerComponents,
  usuarioRepo:              UsuarioRepository
)(implicit ec: ExecutionContext) extends BaseController {

  val loginForm: Form[LoginForm] = Form(
    mapping(
      "alias"    -> nonEmptyText,
      "password" -> nonEmptyText
    )(LoginForm.apply)(LoginForm.unapply)
  )

  // ── GET /login ─────────────────────────────────────────────────────────────

  def loginPage() = Action { implicit request =>
    if (request.session.get("alias").isDefined)
      Redirect(routes.HomeController.index())
    else
      Ok(views.html.login(loginForm))
  }

  // ── POST /login ────────────────────────────────────────────────────────────

  def loginSubmit() = Action.async { implicit request =>
    loginForm.bindFromRequest().fold(

      formConErrores =>
        Future.successful(
          BadRequest(views.html.login(formConErrores))
        ),

      datos => {
        usuarioRepo.buscarPorAlias(datos.alias).map {

          case Some(usuario) if verificarPassword(datos.password, usuario.passwordHash) =>
            Redirect(routes.HomeController.index())
              .withSession(
                "alias"  -> usuario.alias,
                "rol"    -> usuario.rol,
                "nombre" -> usuario.nombre
              )

          case _ =>
            Redirect(routes.AuthController.loginPage())
              .flashing("error" -> "Alias o contraseña incorrectos.")
        }
      }
    )
  }

  // ── GET /logout ────────────────────────────────────────────────────────────

  def logout() = Action { implicit request =>
    Redirect(routes.AuthController.loginPage())
      .withNewSession
      .flashing("info" -> "Sesión cerrada correctamente.")
  }

  // ── Verifica password contra hash BCrypt ───────────────────────────────────
  // Python bcrypt genera prefijo $2b$, at.favre.lib trabaja con $2a$
  // Normalizamos el prefijo antes de verificar para que sean compatibles
  private def verificarPassword(password: String, hash: String): Boolean = {
    val hashNormalizado = if (hash.startsWith("$2b$")) hash.replace("$2b$", "$2a$") else hash
    BCrypt.verifyer().verify(password.toCharArray, hashNormalizado).verified
  }
}