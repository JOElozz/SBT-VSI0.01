package models

import javax.inject.{Inject, Singleton}
import play.api.db.slick.DatabaseConfigProvider
import slick.jdbc.JdbcProfile
import scala.concurrent.{Future, ExecutionContext}

// 1. El Modelo de Datos (Case Class)
case class Historial(id: Option[Long] = None, trabajador: String, timestamp: String, resultado: String, fase: String, faltante: Option[String])

@Singleton
class HistorialRepository @Inject()(dbConfigProvider: DatabaseConfigProvider)(implicit ec: ExecutionContext) {
  
  private val dbConfig = dbConfigProvider.get[JdbcProfile]
  import dbConfig._
  import profile.api._

  // 2. El Mapeo de la Tabla
  private class HistorialTable(tag: Tag) extends Table[Historial](tag, "historial") {
    def id = column[Long]("id", O.PrimaryKey, O.AutoInc)
    def trabajador = column[String]("trabajador")
    def timestamp = column[String]("timestamp")
    def resultado = column[String]("resultado")
    def fase = column[String]("fase")
    def faltante = column[Option[String]]("faltante")

    def * = (id.?, trabajador, timestamp, resultado, fase, faltante) <> ((Historial.apply _).tupled, Historial.unapply)
  }

  private val historial = TableQuery[HistorialTable]

  // 3. Las Funciones para consultar (Queries)
  
  // Obtener todo el historial
  def listarTodo(): Future[Seq[Historial]] = db.run {
    historial.result
  }

  // Guardar un nuevo registro
  def crear(registro: Historial): Future[Long] = db.run {
    (historial returning historial.map(_.id)) += registro
  }
}