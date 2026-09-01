import asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app
from database.seeds.seed_data import seed_database

def test_vehicle_journey_reconstruction_api():
    async def _run():
        await seed_database()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/vehicles/GJ01AB1234/journey")
            assert response.status_code == 200
            data = response.json()
            assert data["plate_number"] == "GJ01AB1234"
            assert data["watchlist_status"] == "STOLEN"
            assert len(data["journey_steps"]) >= 4
            assert len(data["route_coordinates"]) >= 4
    asyncio.run(_run())

def test_sentinel_ingest_catalog_contract():
    async def _run():
        await seed_database()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/ingest")
            assert response.status_code == 200
            catalog = response.json()
            assert len(catalog) >= 4
            for item in catalog:
                assert "id" in item
                assert "rtsp_url" in item
                assert "codec" in item
    asyncio.run(_run())
