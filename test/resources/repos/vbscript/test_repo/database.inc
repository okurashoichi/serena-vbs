' Database Include File
' Common database functions for ASP applications

Option Explicit

' Database configuration constants
Const DB_SERVER = "localhost"
Const DB_NAME = "testdb"
Const DB_USER = "admin"

' Get database connection string
Function GetConnectionString()
    GetConnectionString = "Provider=SQLOLEDB;Data Source=" & DB_SERVER & _
                         ";Initial Catalog=" & DB_NAME & _
                         ";User ID=" & DB_USER
End Function

' Execute a SQL query and return recordset
Function ExecuteQuery(sql)
    Dim conn, rs
    Set conn = Server.CreateObject("ADODB.Connection")
    Set rs = Server.CreateObject("ADODB.Recordset")

    conn.Open GetConnectionString()
    rs.Open sql, conn

    Set ExecuteQuery = rs
End Function

' Execute a non-query SQL command
Sub ExecuteNonQuery(sql)
    Dim conn
    Set conn = Server.CreateObject("ADODB.Connection")
    conn.Open GetConnectionString()
    conn.Execute sql
    conn.Close
    Set conn = Nothing
End Sub

' Escape string for SQL
Function EscapeSql(value)
    EscapeSql = Replace(value, "'", "''")
End Function

' Build INSERT statement
Function BuildInsertStatement(tableName, fields, values)
    Dim sql
    sql = "INSERT INTO " & tableName & " (" & fields & ") VALUES (" & values & ")"
    BuildInsertStatement = sql
End Function

' Build SELECT statement
Function BuildSelectStatement(tableName, fields, whereClause)
    Dim sql
    sql = "SELECT " & fields & " FROM " & tableName
    If whereClause <> "" Then
        sql = sql & " WHERE " & whereClause
    End If
    BuildSelectStatement = sql
End Function

' Check if recordset has data
Function HasData(rs)
    If rs.EOF And rs.BOF Then
        HasData = False
    Else
        HasData = True
    End If
End Function

' Close recordset and connection safely
Sub CloseRecordset(rs)
    If Not rs Is Nothing Then
        If rs.State = 1 Then rs.Close
        Set rs = Nothing
    End If
End Sub
