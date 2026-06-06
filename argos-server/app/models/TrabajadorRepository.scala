package models

import javax.inject.{Inject, Singleton}
import play.api.db.slick.DatabaseConfigProvider
import slick.jdbc.JdbcProfile
import scala.concurrent.{Future, ExecutionContext}

case class Trabajador(alias: String, nombreReal: String)

@Singleton
class TrabajadorRepository @Inject()(dbConfigProvider: DatabaseConfigProvider)(implicit ec: ExecutionContext) {

  private val dbConfig = dbConfigProvider.get[JdbcProfile]
  import dbConfig._
  import profile.api._

  private class TrabajadorTable(tag: Tag) extends Table[Trabajador](tag, "trabajadores") {
    def alias = column[String]("alias", O.PrimaryKey)
    def nombreReal = column[String]("nombre_real")

    def * = (alias, nombreReal) <> ((Trabajador.apply _).tupled, Trabajador.unapply)
  }

  private val trabajadores = TableQuery[TrabajadorTable]

  def listarTodo(): Future[Seq[Trabajador]] = db.run(trabajadores.result)

  def buscarPorAlias(alias: String): Future[Option[Trabajador]] = db.run(
    trabajadores.filter(_.alias === alias).result.headOption
  )

  def crear(trabajador: Trabajador): Future[Int] = db.run(
    trabajadores.insertOrUpdate(trabajador)
  )
}
