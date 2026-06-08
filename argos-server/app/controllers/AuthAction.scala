package controllers

import javax.inject._
import play.api.mvc._
import scala.concurrent.{ExecutionContext, Future}

/**
 * AuthAction
 * ----------
 * Action reutilizable que verifica que existe una sesión válida.
 * Si no hay sesión redirige a GET /login.
 *
 * Uso en HomeController:
 *   def historial() = authAction { implicit request => ... }
 *
 * El request enriquecido expone:
 *   request.alias  — alias del usuario logueado
 *   request.rol    — "supervisor" | "admin"
 */

// Request enriquecido con datos del usuario autenticado
class AuthenticatedRequest[A](
  val alias:   String,
  val rol:     String,
  val nombre:  String,
  request:     Request[A]
) extends WrappedRequest[A](request)

@Singleton
class AuthAction @Inject()(
  val parser: BodyParsers.Default
)(implicit val executionContext: ExecutionContext)
    extends ActionBuilder[AuthenticatedRequest, AnyContent] {

  override def invokeBlock[A](
    request: Request[A],
    block:   AuthenticatedRequest[A] => Future[Result]
  ): Future[Result] = {

    val aliasOpt  = request.session.get("alias")
    val rolOpt    = request.session.get("rol")
    val nombreOpt = request.session.get("nombre")

    (aliasOpt, rolOpt, nombreOpt) match {
      case (Some(alias), Some(rol), Some(nombre)) =>
        block(new AuthenticatedRequest(alias, rol, nombre, request))

      case _ =>
        Future.successful(
          Results.Redirect(routes.AuthController.loginPage())
            .withNewSession
            .flashing("error" -> "Debes iniciar sesión para acceder.")
        )
    }
  }
}

/**
 * AdminAction
 * -----------
 * Igual que AuthAction pero además exige rol == "admin".
 * Útil para rutas de gestión de usuarios.
 */
@Singleton
class AdminAction @Inject()(
  val parser: BodyParsers.Default
)(implicit val executionContext: ExecutionContext)
    extends ActionBuilder[AuthenticatedRequest, AnyContent] {

  override def invokeBlock[A](
    request: Request[A],
    block:   AuthenticatedRequest[A] => Future[Result]
  ): Future[Result] = {

    val aliasOpt  = request.session.get("alias")
    val rolOpt    = request.session.get("rol")
    val nombreOpt = request.session.get("nombre")

    (aliasOpt, rolOpt, nombreOpt) match {
      case (Some(alias), Some("admin"), Some(nombre)) =>
        block(new AuthenticatedRequest(alias, "admin", nombre, request))

      case (Some(_), Some(_), Some(_)) =>
        // Autenticado pero no es admin
        Future.successful(Results.Forbidden("No tienes permisos para acceder a esta sección."))

      case _ =>
        Future.successful(
          Results.Redirect(routes.AuthController.loginPage())
            .withNewSession
            .flashing("error" -> "Debes iniciar sesión para acceder.")
        )
    }
  }
}