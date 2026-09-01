from django.utils.deprecation import MiddlewareMixin


class RazorpayCompatibilityMiddleware(MiddlewareMixin):
    """
    Adds headers required for Razorpay checkout to work in modern Chrome:

    1. Access-Control-Allow-Private-Network: true
       - Fixes Chrome's Private Network Access (PNA) policy that blocks
         Razorpay's fingerprinting requests to localhost/loopback.

    2. Permissions-Policy: accelerometer=*, gyroscope=*, payment=*
       - Fixes the [Violation] Permissions policy violation errors
         thrown by Razorpay's payment iframe.

    3. Cross-Origin-Opener-Policy: unsafe-none
       - Allows Razorpay's popup-based checkout to communicate with
         the parent window (needed for some Razorpay flows).
    """

    def process_request(self, request):
        # Handle Chrome's PNA preflight OPTIONS request
        if request.method == 'OPTIONS' and request.META.get('HTTP_ACCESS_CONTROL_REQUEST_PRIVATE_NETWORK'):
            from django.http import HttpResponse
            response = HttpResponse()
            response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
            response['Access-Control-Allow-Private-Network'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Content-Type, Authorization, X-CSRFToken, '
                'Access-Control-Request-Private-Network'
            )
            response['Access-Control-Max-Age'] = '86400'
            return response
        return None

    def process_response(self, request, response):
        # Allow Razorpay CDN (public origin) to access loopback / localhost
        response['Access-Control-Allow-Private-Network'] = 'true'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = (
            'Content-Type, Authorization, X-CSRFToken, '
            'Access-Control-Request-Private-Network'
        )

        # Allow Razorpay iframe to use device sensors & payment API
        response['Permissions-Policy'] = (
            'accelerometer=*, '
            'gyroscope=*, '
            'magnetometer=*, '
            'payment=*, '
            'camera=*, '
            'microphone=*, '
            'geolocation=*'
        )

        # Allow Razorpay popup to communicate back (cross-origin opener)
        response['Cross-Origin-Opener-Policy'] = 'unsafe-none'

        # Allow Razorpay iframe to embed in our page
        response['Cross-Origin-Embedder-Policy'] = 'unsafe-none'

        # Allow framing from Razorpay domains
        response['X-Frame-Options'] = 'ALLOWALL'

        return response
