#Date: 2025-05-19
from django.urls import path
from django.conf import settings
from . import views

urlpatterns = [
    # Authentication
    path('signup/', views.signup_view,   name='signup'),
    path('login/',  views.login_view,    name='login'),
    path('logout/', views.logout_view,   name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Twilio: your purchased numbers
    path('twilio/numbers/', views.twilio_numbers_view, name='twilio_numbers'),
    path('twilio/call-details/<str:number>/',
         views.get_call_details_by_number,
         name='call_details_by_number'),

    # Twilio: all calls paginated
    path('twilio/all-calls/', views.twilio_all_calls, name='twilio_all_calls'),

    # Twilio: search / buy available numbers (API only)
    path('twilio/search/', views.search_available_numbers, name='search_number'),

    # Twilio: setup‐call (UI & POST)
    path('twilio/setup-call-ui/', views.setup_call_ui, name='setup_call_ui'),
    path('twilio/setup-call/',    views.setup_call,    name='setup_call'),

    # TwiML handler for “setup call”
    path('twilio/twiml-setup-handler/',
         views.twiml_call_handler,
         name='twiml_call_handler'),

    # Twilio: forward‐call (UI & POST)
    path('twilio/forward-call/', views.forward_call_page, name='forward_call_page'),
    path('twilio/forward/',      views.forward_call,      name='forward_call'),

    # TwiML handler for “forwarded call”
    path('twilio/twiml-forward-handler/',
         views.twiml_forward_handler,
         name='twiml_forward_handler'),

    # JSON payload tester (UI & POST)
    path('twilio/send-payload/', views.send_payload_page, name='send_payload_page'),
    path('twilio/payload/',      views.receive_payload,   name='receive_payload'),

 path('test/', views.test_view, name='test'),
   path('test/analyze/', views.analyze_sentiment, name='analyze_sentiment'),

  path("ai-demo/", views.ai_demo_view, name="ai_demo"),


   path("ai-qa/", views.ai_qa_view, name="ai_qa"),
]
