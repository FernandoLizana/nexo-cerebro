package org.nexo.node

import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.RoomDatabase

@Entity(tableName = "quarantine")
data class QuarantineRow(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val beingId: String,
    val summary: String,
    val status: String = "QUARANTINED",
)

@Dao
interface QuarantineDao {
    @Insert
    suspend fun insert(row: QuarantineRow): Long

    @Query("SELECT COUNT(*) FROM quarantine WHERE status = 'QUARANTINED'")
    suspend fun pending(): Int
}

@Database(entities = [QuarantineRow::class], version = 1, exportSchema = false)
abstract class NodeDb : RoomDatabase() {
    abstract fun quarantine(): QuarantineDao
}
