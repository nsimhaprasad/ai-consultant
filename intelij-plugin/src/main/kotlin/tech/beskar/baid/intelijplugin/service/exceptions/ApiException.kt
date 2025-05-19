package tech.beskar.baid.intelijplugin.service.exceptions

import java.lang.RuntimeException

class  ApiException : RuntimeException {
    val statusCode: Int
    val responseBody: String?
    val url: String

    constructor(message: String, statusCode: Int, url: String, responseBody: String? = null) : super(message) {
        this.statusCode = statusCode
        this.url = url
        this.responseBody = responseBody
    }

    constructor(message: String, statusCode: Int, url: String, cause: Throwable, responseBody: String? = null) : super(message, cause) {
        this.statusCode = statusCode
        this.url = url
        this.responseBody = responseBody
    }

    override fun toString(): String {
        return "ApiException: HTTP $statusCode - $message (URL: $url)" +
                if (responseBody != null) "\nResponse: $responseBody" else ""
    }

    companion object {
        fun fromStatusCode(statusCode: Int, url: String, responseBody: String? = null): ApiException {
            val message = when (statusCode) {
                400 -> "Bad Request - The request was malformed or contains invalid parameters"
                401 -> "Unauthorized - Authentication is required or has failed"
                403 -> "Forbidden - You don't have permission to access this resource"
                404 -> "Not Found - The requested resource could not be found"
                409 -> "Conflict - The request couldn't be completed due to a conflict"
                422 -> "Unprocessable Entity - The request was well-formed but contains semantic errors"
                429 -> "Too Many Requests - You've sent too many requests in a given amount of time"
                500 -> "Internal Server Error - Something went wrong on the server"
                502 -> "Bad Gateway - The server received an invalid response from an upstream server"
                503 -> "Service Unavailable - The server is currently unavailable"
                504 -> "Gateway Timeout - The server timed out waiting for a response"
                else -> "HTTP Error $statusCode"
            }

            return ApiException(message, statusCode, url, responseBody)
        }
    }
}