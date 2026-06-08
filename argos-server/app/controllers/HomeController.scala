package controllers

import javax.inject._
import play.api.mvc._
import play.api.libs.json._
import models.{HistorialRepository, Historial, TrabajadorRepository, Trabajador}
import scala.concurrent.ExecutionContext
import java.time.LocalDate
import java.time.format.DateTimeFormatter

@Singleton
class HomeController @Inject()(
  val controllerComponents: ControllerComponents,
  repo:       HistorialRepository,
  trabRepo:   TrabajadorRepository,
  authAction: AuthAction            // ← inyectamos el filtro
)(implicit ec: ExecutionContext) extends BaseController {

  implicit val historialFormat:  OFormat[Historial]  = Json.format[Historial]
  implicit val trabajadorFormat: OFormat[Trabajador] = Json.format[Trabajador]

  // ── GET / — dashboard (protegido) ─────────────────────────────────────────
  def index() = authAction { implicit request =>
    // request.alias  → alias del supervisor logueado
    // request.rol    → "supervisor" | "admin"
    // request.nombre → nombre completo
    Ok(views.html.index())
  }

  // ── POST /auditoria — API Python (NO protegido, viene de red local) ────────
  def recibirAuditoria() = Action.async(parse.json) { implicit request =>
    val body        = request.body
    val timestamp   = (body \ "timestamp").as[String]
    val resultado   = (body \ "resultado").as[String]
    val fase        = (body \ "fase").as[String]
    val faltanteStr = (body \ "faltante").asOpt[String].filter(_.nonEmpty)
    val trabajador  = (body \ "trabajador_id").asOpt[String]
      .orElse((body \ "trabajador").asOpt[String])
      .getOrElse("DESCONOCIDO")

    val nuevoRegistro = Historial(None, trabajador, timestamp, resultado, fase, faltanteStr)
    repo.crear(nuevoRegistro).map { _ =>
      Ok(Json.obj("status" -> "Guardado en Base de Datos SQLite"))
    }
  }

  // ── POST /trabajadores — API Python (NO protegido) ─────────────────────────
  def crearTrabajador() = Action.async(parse.json) { implicit request =>
    val body       = request.body
    val alias      = (body \ "alias").asOpt[String].filter(_.nonEmpty)
    val nombreReal = (body \ "nombre_real").asOpt[String].filter(_.nonEmpty)

    (alias, nombreReal) match {
      case (Some(a), Some(nr)) =>
        trabRepo.crear(Trabajador(a, nr)).map { _ =>
          Ok(Json.obj("status" -> "Trabajador registrado correctamente", "alias" -> a))
        }
      case _ =>
        scala.concurrent.Future.successful(
          BadRequest(Json.obj("error" -> "Debe enviar alias y nombre_real"))
        )
    }
  }

  // ── GET /trabajadores — protegido ──────────────────────────────────────────
  def trabajadores() = authAction.async { implicit request =>
    trabRepo.listarTodo().map(r => Ok(Json.toJson(r)))
  }

  // ── GET /historial — protegido ─────────────────────────────────────────────
  def historial() = authAction.async { implicit request =>
    repo.listarTodo().map { registros =>
      Ok(Json.toJson(registros.map(registroAJson)))
    }
  }

  // ── GET /historial/hoy — protegido ────────────────────────────────────────
  def historialHoy() = authAction.async { implicit request =>
    val hoy = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"))
    repo.listarTodo().map { registros =>
      val deHoy = registros.filter(r => r.timestamp.startsWith(hoy))
      Ok(Json.toJson(deHoy.map(registroAJson)))
    }
  }

  // ── Utilidad ───────────────────────────────────────────────────────────────
  private def registroAJson(r: Historial): JsObject = {
    Json.obj(
      "timestamp"  -> r.timestamp,
      "resultado"  -> r.resultado,
      "fase"       -> r.fase,
      "faltante"   -> r.faltante.getOrElse("-").asInstanceOf[String],
      "trabajador" -> r.trabajador
    )
  }
}