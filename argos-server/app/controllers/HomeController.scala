package controllers

import javax.inject._
import play.api.mvc._
import play.api.libs.json._
import models.{HistorialRepository, Historial} // Importamos el Repositorio y el Modelo
import scala.concurrent.ExecutionContext

@Singleton
class HomeController @Inject()(
  val controllerComponents: ControllerComponents,
  repo: HistorialRepository // Inyectamos la conexión a la base de datos
)(implicit ec: ExecutionContext) extends BaseController {

  // Formato para convertir la clase Historial a JSON y viceversa automáticamente
  implicit val historialFormat: OFormat[Historial] = Json.format[Historial]

  // GET / — página principal (Dashboard de ARGOS)
  def index() = Action { implicit request: Request[AnyContent] =>
    Ok(views.html.index())
  }

  // POST /auditoria — recibe datos de la cámara/Python
  def recibirAuditoria() = Action.async(parse.json) { implicit request =>
    
    // Leemos el JSON que manda Python
    val body = request.body
    val timestamp = (body \ "timestamp").as[String]
    val resultado = (body \ "resultado").as[String]
    val fase      = (body \ "fase").as[String]
    // Python manda string vacío o un valor, en la BD lo guardamos como Option para que pueda ser nulo si no falta nada
    val faltanteStr = (body \ "faltante").asOpt[String].filter(_.nonEmpty) 
    val trabajador = (body \ "trabajador").asOpt[String].getOrElse("DESCONOCIDO")

    // Creamos el objeto y lo guardamos en la Base de Datos
    val nuevoRegistro = Historial(None, trabajador, timestamp, resultado, fase, faltanteStr)
    
    repo.crear(nuevoRegistro).map { _ =>
      // Respondemos a Python que todo salió bien
      Ok(Json.obj("status" -> "Guardado en Base de Datos SQLite"))
    }
  }

  // GET /historial — devuelve las auditorías como JSON al Dashboard
  def historial() = Action.async {
    // Pedimos a la Base de datos todos los registros
    repo.listarTodo().map { registros =>
      
      // Mapeamos los datos para que el Frontend los reciba
      val json = registros.map { r =>
        
        // SOLUCIÓN: Declaramos explícitamente que es un String antes de meterlo al JSON
        val faltanteSeguro: String = r.faltante.getOrElse("-")

        Json.obj(
          "timestamp"  -> r.timestamp,
          "resultado"  -> r.resultado,
          "fase"       -> r.fase,
          "faltante"   -> faltanteSeguro, // Usamos la variable segura
          "trabajador" -> r.trabajador
        )
      }
      
      Ok(Json.toJson(json))
    }
  }
}