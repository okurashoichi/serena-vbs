' VBScript Property Examples
' This file demonstrates Property Get, Let, and Set

Option Explicit

' Class with all property types
Class PropertyDemo
    Private m_StringValue
    Private m_NumberValue
    Private m_ObjectValue
    Private m_ReadOnlyValue

    ' Initialize default values
    Private Sub Class_Initialize()
        m_StringValue = ""
        m_NumberValue = 0
        m_ReadOnlyValue = "Cannot be changed"
    End Sub

    ' Property Get for string value
    Public Property Get StringValue()
        StringValue = m_StringValue
    End Property

    ' Property Let for string value
    Public Property Let StringValue(value)
        m_StringValue = CStr(value)
    End Property

    ' Property Get for number value
    Public Property Get NumberValue()
        NumberValue = m_NumberValue
    End Property

    ' Property Let for number value with validation
    Public Property Let NumberValue(value)
        If IsNumeric(value) Then
            m_NumberValue = CDbl(value)
        End If
    End Property

    ' Property Get for object value
    Public Property Get ObjectValue()
        Set ObjectValue = m_ObjectValue
    End Property

    ' Property Set for object value
    Public Property Set ObjectValue(obj)
        Set m_ObjectValue = obj
    End Property

    ' Read-only property (only Get, no Let)
    Public Property Get ReadOnlyValue()
        ReadOnlyValue = m_ReadOnlyValue
    End Property

    ' Computed property (no backing field)
    Public Property Get IsValid()
        IsValid = (Len(m_StringValue) > 0 And m_NumberValue > 0)
    End Property
End Class

' Class demonstrating indexed properties
Class IndexedPropertyDemo
    Private m_Items(9)
    Private m_Count

    Private Sub Class_Initialize()
        m_Count = 0
    End Sub

    ' Property Get with index parameter
    Public Property Get Item(index)
        If index >= 0 And index < 10 Then
            Item = m_Items(index)
        Else
            Item = Null
        End If
    End Property

    ' Property Let with index parameter
    Public Property Let Item(index, value)
        If index >= 0 And index < 10 Then
            m_Items(index) = value
        End If
    End Property

    ' Count property
    Public Property Get Count()
        Count = m_Count
    End Property

    ' Add item method
    Public Sub AddItem(value)
        If m_Count < 10 Then
            m_Items(m_Count) = value
            m_Count = m_Count + 1
        End If
    End Sub
End Class

' Configuration class with multiple properties
Class Configuration
    Private m_Settings

    Private Sub Class_Initialize()
        Set m_Settings = CreateObject("Scripting.Dictionary")
    End Sub

    Private Sub Class_Terminate()
        Set m_Settings = Nothing
    End Sub

    ' Settings dictionary property
    Public Property Get Settings()
        Set Settings = m_Settings
    End Property

    Public Property Set Settings(obj)
        Set m_Settings = obj
    End Property

    ' Individual setting property
    Public Property Get Setting(key)
        If m_Settings.Exists(key) Then
            Setting = m_Settings(key)
        Else
            Setting = ""
        End If
    End Property

    Public Property Let Setting(key, value)
        If m_Settings.Exists(key) Then
            m_Settings(key) = value
        Else
            m_Settings.Add key, value
        End If
    End Property

    ' Load configuration
    Public Sub LoadDefaults()
        Setting("AppName") = "TestApp"
        Setting("Version") = "1.0.0"
        Setting("Debug") = "false"
    End Sub
End Class
