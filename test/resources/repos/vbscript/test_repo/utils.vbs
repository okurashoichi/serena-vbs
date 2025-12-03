' VBScript Utility Functions
' This file contains common utility functions for testing

Option Explicit

' Calculate the sum of two numbers
Public Function AddNumbers(a, b)
    AddNumbers = a + b
End Function

' Calculate the difference of two numbers
Private Function SubtractNumbers(a, b)
    SubtractNumbers = a - b
End Function

' Multiply two numbers
Function MultiplyNumbers(x, y)
    MultiplyNumbers = x * y
End Function

' Display a message to the user
Public Sub ShowMessage(message)
    WScript.Echo message
End Sub

' Log a message with timestamp
Private Sub LogMessage(msg)
    Dim timestamp
    timestamp = Now()
    WScript.Echo "[" & timestamp & "] " & msg
End Sub

' Initialize the application
Sub InitializeApp()
    LogMessage "Application initialized"
End Sub

' Helper function to validate input
Function ValidateInput(value)
    If IsEmpty(value) Or IsNull(value) Then
        ValidateInput = False
    Else
        ValidateInput = True
    End If
End Function

' Format a number with decimal places
Function FormatNumber(num, decimals)
    FormatNumber = Round(num, decimals)
End Function
