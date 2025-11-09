from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Item, UserProfile, Booking, CROP_CHOICES
from rest_framework import serializers

class UserProfileSerializer(serializers.ModelSerializer):
    crops_list = serializers.SerializerMethodField()
    profile_photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['name', 'phone', 'city', 'address', 'preferred_language', 'crops', 'crops_list', 'profile_photo', 'profile_photo_url']
        extra_kwargs = {'profile_photo': {'write_only': True}}
    
    def get_crops_list(self, obj):
        return obj.get_crops_list()

    def get_profile_photo_url(self, obj):
        # Return just the relative path - frontend will add baseUrl
        if obj.profile_photo and hasattr(obj.profile_photo, 'url'):
            url = obj.profile_photo.url
            print(f"🖼️ Profile photo URL for {obj.user.username}: {url}")
            return url  # Returns: /media/profiles/photo.jpg
        return None

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def user_profile(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=404)
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Update profile
        partial = request.method == 'PATCH'
        
        # Handle crops_list specially
        if 'crops_list' in request.data:
            crops_list = request.data.get('crops_list')
            if isinstance(crops_list, list):
                profile.set_crops_list(crops_list)
            elif isinstance(crops_list, str):
                import json
                try:
                    crops_list = json.loads(crops_list)
                    profile.set_crops_list(crops_list)
                except:
                    pass
        
        # Update other fields
        serializer = UserProfileSerializer(profile, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

@api_view(['POST'])
def register_user(request):
    try:
        user = User.objects.create_user(
            username=request.data['username'],
            email=request.data['email'],
            password=request.data['password']
        )
        return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = AuthTokenSerializer(data=request.data,
                                         context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'username': user.username,
            'email': user.email
        })


from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    name = request.data.get('name')
    phone = request.data.get('phone')
    city = request.data.get('city')
    address = request.data.get('address')
    preferred_language = request.data.get('preferred_language')
    crops = request.data.get('crops', [])  # expect a list of crop keys

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=400)

    user = User.objects.create_user(username=username, password=password, email=email)
    profile = UserProfile.objects.create(
        user=user,
        name=name or '',
        phone=phone or '',
        city=city or '',
        address=address or '',
        preferred_language=preferred_language or 'English',
    )
    if isinstance(crops, list):
        profile.set_crops_list(crops)
        profile.save()
    token = Token.objects.create(user=user)

    return Response({'token': token.key, 'username': user.username})

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    from django.contrib.auth import authenticate

    username = request.data.get('username')
    password = request.data.get('password')
    
    print(f"DEBUG - Login attempt for username: '{username}'")
    
    # Validate that username and password are provided
    if not username or not password:
        print("DEBUG - Missing username or password")
        return Response({'error': 'Username and password are required'}, status=400)
    
    # Check if user exists
    try:
        user_exists = User.objects.filter(username=username).exists()
        print(f"DEBUG - User '{username}' exists: {user_exists}")
    except Exception as e:
        print(f"DEBUG - Error checking user: {e}")
    
    user = authenticate(username=username, password=password)
    
    print(f"DEBUG - Authentication result: {user}")

    if user is None:
        print("DEBUG - Authentication failed - Invalid credentials")
        return Response({'error': 'Invalid credentials'}, status=400)

    token, created = Token.objects.get_or_create(user=user)
    # Get full name from profile if exists
    name = ''
    try:
        name = user.profile.name
    except Exception:
        name = user.username
    
    print(f"DEBUG - Login successful for user: {user.username}")
    return Response({'token': token.key, 'username': user.username, 'name': name})


from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def home(request):
    return render(request, 'home.html')


# Items API
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def items(request):
    if request.method == 'GET':
        item_type = request.query_params.get('type')  # 'marketplace' or 'rental'
        queryset = Item.objects.all().order_by('-created_at')
        if item_type in ['marketplace', 'rental']:
            queryset = queryset.filter(item_type=item_type)

        def serialize(item: Item):
            # Try to get owner's profile
            profile = None
            try:
                profile = item.owner.profile
            except Exception:
                pass
            return {
                'id': item.id,
                'item_type': item.item_type,
                'name': item.name,
                'description': item.description,
                'price': str(item.price),
                'per_unit': item.per_unit,
                'operator_available': item.operator_available,
                'image_url': item.image.url if item.image else None,  # Return relative path only
                'owner': item.owner.username if item.owner_id else None,
                'owner_name': profile.name if profile else '',
                'owner_phone': profile.phone if profile else '',
                'location': profile.city if profile else '',
                'created_at': item.created_at.isoformat(),
                'availability_start': item.availability_start.isoformat() if item.availability_start else None,
                'availability_end': item.availability_end.isoformat() if item.availability_end else None,
                'time_slots': item.time_slots,
                'owner_address': profile.address if profile else '',
            }

        return Response([serialize(i) for i in queryset])

    # POST create
    owner = request.user if request.user and request.user.is_authenticated else None
    # Accept both form-data and JSON
    data = request.data
    item_type = data.get('item_type')
    name = data.get('name')
    description = data.get('description', '')
    price = data.get('price')
    per_unit = data.get('per_unit')  # optional
    operator_available = str(data.get('operator_available', 'false')).lower() in ['true', '1', 'yes']
    image = data.get('image')
    availability_start = data.get('availability_start')
    availability_end = data.get('availability_end')
    time_slots = data.get('time_slots')

    if item_type not in ['marketplace', 'rental']:
        return Response({'error': 'item_type must be marketplace or rental'}, status=400)
    if not name or not price:
        return Response({'error': 'name and price are required'}, status=400)

    if item_type == 'rental' and per_unit not in ['hour', 'acre', 'day']:
        return Response({'error': 'per_unit must be one of hour, acre, day for rental'}, status=400)

    if owner is None:
        # Allow anonymous owner for simplicity; set to first user or None
        owner = User.objects.first()

    # Parse dates and time_slots
    from datetime import date
    import json
    avail_start = None
    avail_end = None
    slots = None
    try:
        if availability_start:
            avail_start = date.fromisoformat(availability_start[:10])
        if availability_end:
            avail_end = date.fromisoformat(availability_end[:10])
        if time_slots:
            slots = json.loads(time_slots) if isinstance(time_slots, str) else time_slots
    except Exception as e:
        return Response({'error': f'Invalid date or time_slots: {e}'}, status=400)

    item = Item.objects.create(
        owner=owner,
        item_type=item_type,
        name=name,
        description=description,
        price=price,
        per_unit=per_unit if item_type == 'rental' else None,
        operator_available=operator_available if item_type == 'rental' else False,
        image=image,
        availability_start=avail_start,
        availability_end=avail_end,
        time_slots=slots,
    )

    return Response({'id': item.id}, status=201)

class BookingSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.profile.name', read_only=True, default='')
    user_phone = serializers.CharField(source='user.profile.phone', read_only=True, default='')
    item_name = serializers.CharField(source='item.name', read_only=True, default='')
    class Meta:
        model = Booking
        fields = ['id', 'item', 'item_name', 'user', 'user_name', 'user_phone', 'date', 'time_slot', 'status', 'contact_phone', 'contact_name', 'created_at']

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def bookings(request):
    if request.method == 'GET':
        item_id = request.query_params.get('item_id')
        if item_id:
            qs = Booking.objects.filter(item_id=item_id).order_by('-created_at')
        else:
            qs = Booking.objects.filter(user=request.user).order_by('-created_at')
        return Response(BookingSerializer(qs, many=True).data)
    # POST: create booking(s)
    data = request.data
    item_id = data.get('item')
    date = data.get('date')
    time_slots = data.get('time_slots')
    contact_phone = data.get('contact_phone')
    contact_name = data.get('contact_name')
    if not (item_id and date and time_slots and contact_phone and contact_name):
        return Response({'error': 'Missing required fields'}, status=400)
    if not isinstance(time_slots, list) or not time_slots:
        return Response({'error': 'time_slots must be a non-empty list'}, status=400)
    created = []
    for slot in time_slots:
        # Block slot if any booking is pending or accepted
        if Booking.objects.filter(item_id=item_id, date=date, time_slot=slot, status__in=[Booking.Status.PENDING, Booking.Status.ACCEPTED]).exists():
            continue  # skip already booked slots
        booking = Booking.objects.create(
            item_id=item_id,
            user=request.user,
            date=date,
            time_slot=slot,
            contact_phone=contact_phone,
            contact_name=contact_name,
            status=Booking.Status.PENDING,
        )
        created.append(booking)
    if not created:
        return Response({'error': 'All selected slots are already booked or pending confirmation'}, status=400)
    return Response(BookingSerializer(created, many=True).data, status=201)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_booking(request, booking_id):
    # Only owner can accept/decline
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=404)
    if booking.item.owner != request.user:
        return Response({'error': 'Not authorized'}, status=403)
    action = request.data.get('action')  # 'accept' or 'decline'
    if action == 'accept':
        booking.status = Booking.Status.ACCEPTED
    elif action == 'decline':
        booking.status = Booking.Status.DECLINED
    else:
        return Response({'error': 'Invalid action'}, status=400)
    booking.save()
    return Response({'status': booking.status})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def owner_bookings(request):
    bookings = Booking.objects.filter(item__owner=request.user).order_by('-created_at')
    return Response(BookingSerializer(bookings, many=True).data)
