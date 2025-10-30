"""
Health check API controller
"""
from flask_restx import Resource, fields
from app.api.v1 import api
from app.utils.database import check_database_connection, get_connection_pool_status, get_connection_stats, cleanup_connections
from app.utils.response import success_response, error_response
import psutil
import datetime
from typing import Dict, Any, List

# API Models
health_model = api.model('Health', {
    'status': fields.String(description='Overall health status'),
    'database': fields.Boolean(description='Database connection status'),
    'pool_status': fields.Raw(description='Connection pool status'),
    'connection_stats': fields.Raw(description='Detailed connection statistics'),
    'memory_usage': fields.Float(description='Memory usage percentage'),
    'cpu_usage': fields.Float(description='CPU usage percentage'),
    'timestamp': fields.DateTime(description='Health check timestamp')
})

@api.route('/health')
class HealthCheck(Resource):
    @api.doc('health_check')
    @api.marshal_with(health_model)
    def get(self) -> tuple:
        """Get application health status"""
        try:
            # Check database connection
            db_healthy = check_database_connection()
            
            # Get connection pool status
            pool_status = get_connection_pool_status()
            connection_stats = get_connection_stats()
            
            # Get system metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Determine overall status
            overall_status = "healthy" if db_healthy else "unhealthy"
            
            health_data = {
                "status": overall_status,
                "database": db_healthy,
                "pool_status": pool_status,
                "connection_stats": connection_stats,
                "memory_usage": round(memory.percent, 2),
                "cpu_usage": round(cpu_percent, 2),
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
            
            return success_response(health_data), 200 if db_healthy else 503
            
        except Exception as e:
            error_data = {
                "status": "error",
                "error": str(e),
                "database": False,
                "pool_status": {},
                "connection_stats": {},
                "memory_usage": 0,
                "cpu_usage": 0,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
            return error_response(error_data, str(e)), 500

@api.route('/health/connections')
class ConnectionManagement(Resource):
    @api.doc('get_connection_stats')
    def get(self) -> tuple:
        """Get detailed connection statistics"""
        try:
            stats = get_connection_stats()
            pool_status = get_connection_pool_status()
            
            response_data = {
                "connection_stats": stats,
                "pool_status": pool_status,
                "recommendations": self._get_recommendations(stats)
            }
            
            return success_response(response_data), 200
        except Exception as e:
            return error_response(str(e)), 500
    
    @api.doc('cleanup_connections')
    def post(self) -> tuple:
        """Clean up and reset all database connections"""
        try:
            success = cleanup_connections()
            if success:
                return success_response(None, "Connections cleaned up successfully"), 200
            else:
                return error_response("Failed to clean up connections"), 500
        except Exception as e:
            return error_response(str(e)), 500
    
    def _get_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Get recommendations based on connection stats"""
        recommendations = []
        
        # Parse utilization percentage
        utilization_str = stats.get('pool_utilization', '0%')
        utilization = float(utilization_str.replace('%', ''))
        
        if utilization > 80:
            recommendations.append("High pool utilization - consider increasing pool size")
        
        if stats.get('invalid_connections', 0) > 0:
            recommendations.append("Invalid connections detected - consider cleanup")
        
        if stats.get('temporary_connections', 0) > 3:
            recommendations.append("Many temporary connections - consider increasing permanent pool size")
        
        if not recommendations:
            recommendations.append("Connection pool is healthy")
        
        return recommendations
