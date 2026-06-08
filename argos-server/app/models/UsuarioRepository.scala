package models

import javax.inject._
import play.api.db.slick.DatabaseConfigProvider
import slick.jdbc.JdbcProfile
import scala.concurrent.{ExecutionContext, Future}

// ── Modelo ────────────────────────────────────────────────────────────────────

case class Usuario(
  id:            Option[Long],
  alias:         String,
  nombre:        String,
  passwordHash:  String,
  rol:           String,   // "supervisor" | "admin"
  activo:        Boolean
)

// ── Repositorio ───────────────────────────────────────────────────────────────

@Singleton
class UsuarioRepository @Inject()(
  dbConfigProvider: DatabaseConfigProvider
)(implicit ec: ExecutionContext) {

  private val dbConfig = dbConfigProvider.get[JdbcProfile]
  import dbConfig._
  import profile.api._

  private class UsuariosTable(tag: Tag) extends Table[Usuario](tag, "usuarios") {
    def id           = column[Long]("id", O.PrimaryKey, O.AutoInc)
    def alias        = column[String]("alias")
    def nombre       = column[String]("nombre")
    def passwordHash = column[String]("password_hash")
    def rol          = column[String]("rol")
    def activo       = column[Boolean]("activo")

    def * = (id.?, alias, nombre, passwordHash, rol, activo).mapTo[Usuario]
  }

  private val usuarios = TableQuery[UsuariosTable]

  /** Busca un usuario por alias (case-insensitive). */
  def buscarPorAlias(alias: String): Future[Option[Usuario]] =
    db.run(
      usuarios
        .filter(u => u.alias.toUpperCase === alias.trim.toUpperCase && u.activo === true)
        .result
        .headOption
    )

  /** Crea un nuevo usuario. El hash debe venir ya generado con BCrypt. */
  def crear(usuario: Usuario): Future[Unit] =
    db.run(usuarios += usuario).map(_ => ())

  /** Lista todos los usuarios activos. */
  def listarTodo(): Future[Seq[Usuario]] =
    db.run(usuarios.filter(_.activo === true).result)

  /** Desactiva un usuario (baja lógica, no borra el registro). */
  def desactivar(alias: String): Future[Int] =
    db.run(
      usuarios
        .filter(_.alias.toUpperCase === alias.trim.toUpperCase)
        .map(_.activo)
        .update(false)
    )
}