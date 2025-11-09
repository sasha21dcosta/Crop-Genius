"""
Django management command to generate weather-based disease alerts

Usage:
    python manage.py generate_weather_alerts
    python manage.py generate_weather_alerts --force-refresh
    
This command can be scheduled to run daily using:
- Cron jobs (Linux/Mac)
- Task Scheduler (Windows)
- Celery Beat (for production)
"""

from django.core.management.base import BaseCommand
from weather_alerts.utils import generate_alerts_for_all_users


class Command(BaseCommand):
    help = 'Generate weather-based disease alerts for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help='Force refresh weather data even if cached data exists',
        )

    def handle(self, *args, **options):
        force_refresh = options['force_refresh']
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('🌦️  WEATHER-BASED DISEASE ALERT GENERATION'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        if force_refresh:
            self.stdout.write(self.style.WARNING('Force refresh enabled - will fetch new weather data'))
        
        try:
            # Generate alerts for all users
            stats = generate_alerts_for_all_users(force_refresh)
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ Alert generation completed successfully!'))
            self.stdout.write('')
            self.stdout.write(f"📊 Statistics:")
            self.stdout.write(f"   Total users with crops: {stats['total_users']}")
            self.stdout.write(f"   Users processed: {stats['users_processed']}")
            self.stdout.write(f"   Total alerts generated: {stats['total_alerts']}")
            self.stdout.write('')
            
            if stats['total_alerts'] > 0:
                avg_alerts = stats['total_alerts'] / max(stats['users_processed'], 1)
                self.stdout.write(f"   Average alerts per user: {avg_alerts:.1f}")
            
            self.stdout.write(self.style.SUCCESS('=' * 60))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error generating alerts: {e}'))
            raise

