#Date: 2025-05-19
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseNotAllowed, JsonResponse ,HttpResponse
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from django.conf import settings
from django.core.paginator import Paginator
from urllib.parse import unquote
import logging
from transformers import pipeline
import openai
from openai import RateLimitError, OpenAIError
from django.urls import reverse
logger = logging.getLogger(__name__)
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
openai.api_key = settings.OPENAI_API_KEY
#SIGNUP******************************
@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        first = request.POST.get('first_name')
        last = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        is_api = (
            request.headers.get('Accept') == 'application/json'
            or request.content_type == 'application/json'
        )

        if len(password) < 8:
            if is_api:
                return JsonResponse({'success': False, 'message': 'Password must be at least 8 characters'}, status=400)
            else:
                return render(request, 'signup.html', {'error': 'Password must be at least 8 characters'})

        if User.objects.filter(username=email).exists():
            if is_api:
                return JsonResponse({'success': False, 'message': 'User already exists'}, status=400)
            else:
                return render(request, 'signup.html', {'error': 'User already exists'})

        # Create the user
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first,
            last_name=last,
            password=password
        )

        if is_api:
            return JsonResponse({'success': True, 'message': 'Account created successfully'}, status=201)
        else:
            return redirect('login')

    return render(request, 'signup.html')

#LOGIN******************************
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            auth_login(request, user)

            # ✅ Check if it's JSON (API) request
            if request.headers.get('Accept') == 'application/json' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'username': user.username,
                        'email': user.email
                    }
                })

            # ✅ Otherwise, redirect for browser
            return redirect('dashboard')

        else:
            if request.headers.get('Accept') == 'application/json' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'message': 'Invalid credentials'}, status=401)
            messages.error(request, 'Invalid credentials.')

    return render(request, 'login.html')
#Dashboard******************************
@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html', {'user': request.user})

#Logout******************************
@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        auth_logout(request)

        # Handle API (Postman) vs browser redirect
        if request.headers.get('Accept') == 'application/json' or request.content_type == 'application/json':
            return JsonResponse({'success': True, 'message': 'Logged out successfully'}, status=200)
        else:
            return redirect('login')

    return HttpResponseNotAllowed(['POST'], 'Method Not Allowed')


#To show twilio available numbers******************************
@login_required
def twilio_numbers_view(request):
    incoming_numbers = client.incoming_phone_numbers.list() #Calls Twilio API to get all your purchased incoming phone numbers.

    #Prepares a context dictionary with only the phone numbers.
    context = {
        'numbers': [num.phone_number for num in incoming_numbers]
    }  
    

    return render(request, 'twilio_numbers.html', context)


# Get Call Details Number Wise******************************
@csrf_exempt
@login_required
def get_call_details_by_number(request, number):
    decoded_number = unquote(number)   # Converts URL-encoded numbers (like %2B for +) to normal.

    # You can fetch more if needed (up to 1000 or 3000)
    calls = client.calls.stream(limit=300)  # Streams last 300 call records.Increase if you want more history

    def format_duration(seconds):  #converts seconds to a user-friendly string.
        seconds = int(seconds or 0)
        return f"{seconds} sec" if seconds < 60 else f"{seconds // 60} min {seconds % 60} sec"

#Filters calls where the number matches either from or to.
    filtered_calls = [
        {
            'sid': c.sid,
            'date': c.start_time.strftime("%Y-%m-%d %H:%M:%S") if c.start_time else 'N/A',
            'status': c.status,
            'direction': c.direction,
            'from': getattr(c, 'from_', getattr(c, '_from', 'N/A')),
            'to': c.to,
            'type': 'Phone',
            'duration': format_duration(c.duration),
            'stir_status': c.__dict__.get('stir_verification', '—')

        }
        #For each call, it creates a dictionary with call details for the template.
        for c in calls
        if getattr(c, 'from_', getattr(c, '_from', '')) == decoded_number or c.to == decoded_number
    ]
# Renders the call_details.html page with this data.
    return render(request, 'call_details.html', {
        'number': decoded_number,
        'calls': filtered_calls
    })

# Twilio All Calls******************************
@login_required
def twilio_all_calls(request):
    page = int(request.GET.get('page', 1))
    page_size = 10
    start = (page - 1) * page_size

    calls = client.calls.list(limit=2500)  # Fetch a chunk to paginate manually
    paginated_calls = calls[start:start + page_size]

    def format_duration(seconds):
        seconds = int(seconds or 0)
        return f"{seconds} sec" if seconds < 60 else f"{seconds // 60} min {seconds % 60} sec"

    call_data = [{
        'sid': c.sid,
        'date': c.start_time.strftime("%Y-%m-%d %H:%M:%S") if c.start_time else 'N/A',
        'status': c.status,
        'direction': c.direction,
        # 'direction': map_direction(c.direction),
        'from': c._from,
        'to': c.to,
        'type': 'Phone',
        'duration': format_duration(c.duration),
        'stir_status': getattr(c, 'stir_verification', '—')
    } for c in paginated_calls]

    total = len(calls)
    total_pages = (total + page_size - 1) // page_size

    context = {
        'calls': call_data,
        'page': page,
        'total_pages': total_pages,
        'serial_start': start + 1
    }
    return render(request, 'twilio_all_calls.html', context)

#Buy a Number******************************
@csrf_exempt
@login_required
def search_available_numbers(request):
    if request.method == 'GET':
        numbers = client.available_phone_numbers('US').local.list(limit=5)
        return JsonResponse({
            'success': True,
            'numbers': [n.phone_number for n in numbers]
        })
    return HttpResponseNotAllowed(['GET'])

#Setup Call******************************
@csrf_exempt
def setup_call(request):
    if request.method == 'POST':
        from_number = settings.TWILIO_DEFAULT_NUMBER
        to_number   = request.POST['to']

        # Build the *public* URL for your TwiML handler,
        # including the /auth/ prefix:
        handler_path = reverse('twiml_call_handler')  # => '/auth/twilio/twiml-call-handler/'
        handler_url  = request.build_absolute_uri(handler_path)
        
        call = client.calls.create(
          to    = to_number,
          from_ = from_number,
          url   = handler_url
        )
        return JsonResponse({'success': True, 'call_sid': call.sid})
    return HttpResponseNotAllowed(['POST'])

logger = logging.getLogger(__name__)

@csrf_exempt
def twiml_call_handler(request):
    logger.info("Received TwiML request")

    # Create the TwiML response
    response = VoiceResponse()
    
    # Log the TwiML response for debugging
    logger.info(f"TwiML Response: {str(response)}")

    # Example: Play a message and then hang up
    response.say("Hello, this is your call from Twilio. Goodbye!")
    response.hangup()

    return HttpResponse(str(response), content_type='text/xml')
# @csrf_exempt  
def setup_call_ui(request):
    return render(request, 'setup_call.html')


#BELOW CODE IF FOR TESTING PURPOSES ONLY(here i am getting two call on one api hit)
# @csrf_exempt
# def setup_call(request):
#     if request.method == 'POST':
#         from_number = settings.TWILIO_DEFAULT_NUMBER
#         to_number   = request.POST['to']

#         # Build the *public* URL for your TwiML handler, include the to_number as query param
#         handler_path = reverse('twiml_call_handler')  # '/auth/twilio/twiml-call-handler/'
#         base_handler_url  = request.build_absolute_uri(handler_path)
#         handler_url = f"{base_handler_url}?to={to_number}"

#         call = client.calls.create(
#           to    = to_number,
#           from_ = from_number,
#           url   = handler_url
#         )
#         return JsonResponse({'success': True, 'call_sid': call.sid})
#     return HttpResponseNotAllowed(['POST'])
# @csrf_exempt
# def twiml_call_handler(request):
#     logger.info("Received TwiML request")

#     to_number = request.GET.get('to')
#     if not to_number:
#         # fallback message if no 'to' param present
#         response = VoiceResponse()
#         response.say("Sorry, no number to dial. Goodbye!")
#         response.hangup()
#         return HttpResponse(str(response), content_type='text/xml')

#     response = VoiceResponse()
#     dial = response.dial(callerId=settings.TWILIO_DEFAULT_NUMBER)
#     dial.number(to_number)  # dynamically dial the requested number

#     logger.info(f"TwiML Response: {str(response)}")
#     return HttpResponse(str(response), content_type='text/xml')



#Forward Call******************************
# @csrf_exempt
# @login_required
# def forward_call(request):
#     """
#     Called by your form POST. Kicks off a Twilio call that
#     fetches TwiML from `twiml_call_handler`.
#     """
#     if request.method == 'POST':
#         to_number   = request.POST.get('to')
#         from_number = settings.TWILIO_DEFAULT_NUMBER

#         if not to_number:
#             return JsonResponse({'success': False, 'error': 'Missing destination number'}, status=400)

#         # Build absolute URL to our public TwiML endpoint
#         twiml_url = request.build_absolute_uri(reverse('twiml_forward_handler'))

#         call = client.calls.create(
#             to    = to_number,
#             from_ = from_number,
#             url   = twiml_url
#         )
#         return JsonResponse({'success': True, 'call_sid': call.sid})

#     return HttpResponseNotAllowed(['POST'])
@csrf_exempt
@login_required
def forward_call(request):
    """
    Called by your form POST. Initiates a Twilio call from TWILIO_DEFAULT_NUMBER
    directly to the forwarding number, without calling the input number first.
    """
    if request.method == 'POST':
        # The number you want to forward calls to (hardcoded or from config)
        forward_to_number = '+919317260007'  # Replace with your desired forwarding number
        
        from_number = settings.TWILIO_DEFAULT_NUMBER
        
        # URL for TwiML to control the call, if needed (you can just dial directly)
        twiml_url = request.build_absolute_uri(reverse('twiml_forward_handler'))
        
        # Create a call from your Twilio number to the forward_to_number
        call = client.calls.create(
            to=forward_to_number,
            from_=from_number,
            url=twiml_url
        )
        return JsonResponse({'success': True, 'call_sid': call.sid})
    
    return HttpResponseNotAllowed(['POST'])


@csrf_exempt
def twiml_forward_handler(request):
    """
    Twilio GETs here for TwiML instructions (public, no auth).
    """
    resp = VoiceResponse()
    resp.say("Hello, this is your forwarded call. Goodbye!")
    resp.hangup()
    return HttpResponse(str(resp), content_type='application/xml')

@login_required
def forward_call_page(request):
    """
    Renders the “Forward a Call” form.
    """
    return render(request, 'forward_call.html')


#Receive JSON Payload******************************
@csrf_exempt
@login_required
def receive_payload(request):
    if request.method == 'POST':
        try:
            import json
            # data = json.loads(request.body)
            raw_payload = request.POST.get("payload", "")
            data = json.loads(raw_payload)
            return JsonResponse({'success': True, 'received': data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return HttpResponseNotAllowed(['POST'])

@login_required
def send_payload_page(request):
    return render(request, 'send_payload.html')


sentiment = pipeline("sentiment-analysis")

@login_required
def test_view(request):
    # Simply render your test.html “Hello world” page
    return render(request, 'test.html')

@csrf_exempt
def analyze_sentiment(request):
    if request.method == "POST":
        text = request.POST.get("text", "")
        if not text:
            return JsonResponse({"error": "Please provide some text."}, status=400)

        result = sentiment(text[:512])[0]
        # result example: {"label":"POSITIVE","score":0.9987}
        return JsonResponse(result)
    return HttpResponseNotAllowed(["POST"])



generator = pipeline("text-generation", model="gpt2", framework="pt")  
@csrf_exempt
@login_required
def ai_demo_view(request):
    generated = None
    prompt = ""
    if request.method == "POST":
        prompt = request.POST.get("prompt", "").strip()
        if prompt:
            # Generate up to 50 tokens total (prompt + continuation)
            outputs = generator(prompt, max_length=50, num_return_sequences=1)
            generated = outputs[0]["generated_text"]

    return render(request, "text_gen.html", {
        "prompt": prompt,
        "generated": generated,
    })


# qa_pipeline = pipeline("text2text-generation", model="google/flan-t5-small")
# @csrf_exempt
# @login_required
# def ai_qa_view(request):
#     question = ""
#     answer = ""
#     if request.method == "POST":
#         question = request.POST.get("question", "").strip()
#         if question:
#             # prepend the instruction
#             prompt = f"Answer the question: {question}"
#             out = qa_pipeline(prompt, max_length=64, num_return_sequences=1)[0]["generated_text"]
#             answer = out
#     return render(request, "ai_qa.html", {
#         "question": question,
#         "answer": answer
#     })


@csrf_exempt
@login_required
def ai_qa_view(request):
    question = ""
    answer = None
    error   = None

    if request.method == "POST":
        question = request.POST.get("question", "").strip()
        if question:
            try:
                resp = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": question}],
                )
                answer = resp.choices[0].message.content
            except RateLimitError:
                # quota exhausted
                error = "🚧 You’ve hit your OpenAI quota. Please check your plan or billing settings."
            except OpenAIError as e:
                # any other OpenAI-raised exception
                error = f"❗ OpenAI error: {e}"

    return render(request, "ai_qa.html", {
        "question": question,
        "answer":   answer,
        "error":    error,
    })
