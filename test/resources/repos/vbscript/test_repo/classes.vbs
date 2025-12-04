' VBScript Class Definitions
' This file contains class definitions for testing

Option Explicit

' Simple Person class
Class Person
    Private m_Name
    Private m_Age

    ' Constructor-like initialization
    Public Sub Initialize(name, age)
        m_Name = name
        m_Age = age
    End Sub

    ' Name property getter
    Public Property Get Name()
        Name = m_Name
    End Property

    ' Name property setter
    Public Property Let Name(value)
        m_Name = value
    End Property

    ' Age property getter
    Public Property Get Age()
        Age = m_Age
    End Property

    ' Age property setter
    Public Property Let Age(value)
        If value >= 0 Then
            m_Age = value
        End If
    End Property

    ' Get full description
    Public Function GetDescription()
        GetDescription = m_Name & " is " & m_Age & " years old"
    End Function

    ' Check if adult
    Public Function IsAdult()
        IsAdult = (m_Age >= 18)
    End Function
End Class

' Calculator class with multiple operations
Class Calculator
    Private m_Result

    ' Initialize result to zero
    Private Sub Class_Initialize()
        m_Result = 0
    End Sub

    ' Result property getter
    Public Property Get Result()
        Result = m_Result
    End Property

    ' Add a number
    Public Sub Add(value)
        m_Result = m_Result + value
    End Sub

    ' Subtract a number
    Public Sub Subtract(value)
        m_Result = m_Result - value
    End Sub

    ' Multiply by a number
    Public Sub Multiply(value)
        m_Result = m_Result * value
    End Sub

    ' Divide by a number
    Public Function Divide(value)
        If value <> 0 Then
            m_Result = m_Result / value
            Divide = True
        Else
            Divide = False
        End If
    End Function

    ' Reset the calculator
    Public Sub Reset()
        m_Result = 0
    End Sub
End Class

' Database connection class with Set property
Class DatabaseConnection
    Private m_Connection
    Private m_ConnectionString

    ' Connection property with Set
    Public Property Set Connection(obj)
        Set m_Connection = obj
    End Property

    ' Connection property getter
    Public Property Get Connection()
        Set Connection = m_Connection
    End Property

    ' Connection string property
    Public Property Let ConnectionString(value)
        m_ConnectionString = value
    End Property

    Public Property Get ConnectionString()
        ConnectionString = m_ConnectionString
    End Property

    ' Open connection
    Public Function Open()
        ' Simulated connection open
        Open = True
    End Function

    ' Close connection
    Public Sub Close()
        Set m_Connection = Nothing
    End Sub
End Class
