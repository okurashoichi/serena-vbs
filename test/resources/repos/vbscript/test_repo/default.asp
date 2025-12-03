<%@ Language="VBScript" %>
<!DOCTYPE html>
<html>
<head>
    <title>ASP Test Page</title>
</head>
<body>
<%
' Server-side VBScript code in ASP delimiters

Option Explicit

' Get current date formatted
Function GetFormattedDate()
    GetFormattedDate = FormatDateTime(Now(), vbLongDate)
End Function

' Get greeting based on time of day
Function GetGreeting()
    Dim hour
    hour = Hour(Now())

    If hour < 12 Then
        GetGreeting = "Good morning"
    ElseIf hour < 18 Then
        GetGreeting = "Good afternoon"
    Else
        GetGreeting = "Good evening"
    End If
End Function

' Process form data
Sub ProcessForm(formData)
    Dim key
    For Each key In formData
        Response.Write key & " = " & formData(key) & "<br>"
    Next
End Sub

' Validate email address
Function IsValidEmail(email)
    Dim regex
    Set regex = New RegExp
    regex.Pattern = "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    IsValidEmail = regex.Test(email)
    Set regex = Nothing
End Function
%>

<h1><%= GetGreeting() %>, User!</h1>
<p>Today is <%= GetFormattedDate() %></p>

<%
' More server-side code
Sub RenderNavigation()
    Response.Write "<nav>"
    Response.Write "<a href='home.asp'>Home</a>"
    Response.Write "<a href='about.asp'>About</a>"
    Response.Write "<a href='contact.asp'>Contact</a>"
    Response.Write "</nav>"
End Sub

Call RenderNavigation()
%>

<script runat="server">
' Server-side script tag
Class PageHelper
    Private m_Title

    Public Property Let Title(value)
        m_Title = value
    End Property

    Public Property Get Title()
        Title = m_Title
    End Property

    Public Function GetPageHeader()
        GetPageHeader = "<h1>" & m_Title & "</h1>"
    End Function

    Public Sub RenderFooter()
        Response.Write "<footer>Copyright 2024</footer>"
    End Sub
End Class

Function CreateHelper(title)
    Dim helper
    Set helper = New PageHelper
    helper.Title = title
    Set CreateHelper = helper
End Function
</script>

</body>
</html>
