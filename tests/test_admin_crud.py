import pytest
from app.web.routes.api_routes import _parse_ids
from app.database.repositories.warning_repo import WarningRepository
from app.database.repositories.ad_repo import AdvertisementRepository
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.group_repo import GroupRepository
from tests.test_commercial_workflow import get_test_session


def test_parse_ids():
    assert _parse_ids("1,2,3") == [1, 2, 3]
    assert _parse_ids(" 10 , 20 , 30 ") == [10, 20, 30]
    assert _parse_ids("abc, 5, def, 9") == [5, 9]
    assert _parse_ids("") == []
    assert _parse_ids(None) == []


@pytest.mark.asyncio
async def test_user_crud_operations():
    async with get_test_session() as session:
        # Create test user
        user = await UserRepository.get_or_create(
            session,
            telegram_id=98765432101,
            username="test_crud_user",
            first_name="CRUD",
            last_name="Tester"
        )
        assert user.id is not None
        user_id = user.id

        # Update user
        updated = await UserRepository.update_user(
            session,
            user_id,
            first_name="CRUD Updated",
            username="@crud_updated",
            warnings_count=3,
            is_muted=True,
            is_banned=False
        )
        assert updated.first_name == "CRUD Updated"
        assert updated.username == "crud_updated"
        assert updated.warnings_count == 3
        assert updated.is_muted is True

        # Bulk reset
        reset_count = await UserRepository.bulk_reset_warnings(session, [user_id])
        assert reset_count == 1
        refreshed = await UserRepository.get_by_id(session, user_id)
        assert refreshed.warnings_count == 0

        # Delete user
        del_res = await UserRepository.delete_by_id(session, user_id)
        assert del_res is True

        # Verify gone
        gone = await UserRepository.get_by_id(session, user_id)
        assert gone is None


@pytest.mark.asyncio
async def test_group_crud_operations():
    async with get_test_session() as session:
        # Create test group
        group = await GroupRepository.get_or_create(
            session,
            telegram_chat_id=-1009988776655,
            title="CRUD Test Group",
            username="crud_group"
        )
        assert group.id is not None
        group_id = group.id

        # Update group
        updated = await GroupRepository.update_group(
            session,
            group_id,
            title="Updated Title Group",
            username="@new_group_user",
            is_active=False
        )
        assert updated.title == "Updated Title Group"
        assert updated.username == "new_group_user"
        assert updated.is_active is False

        # Delete group
        del_res = await GroupRepository.delete_by_id(session, group_id)
        assert del_res is True

        # Verify gone
        gone = await GroupRepository.get_by_id(session, group_id)
        assert gone is None


@pytest.mark.asyncio
async def test_ad_and_warning_crud_operations():
    async with get_test_session() as session:
        # Setup group and user
        group = await GroupRepository.get_or_create(session, -1001122334455, "Ad Warning Group")
        user = await UserRepository.get_or_create(session, 8877665544, "ad_warning_user")

        # Create Ad
        ad = await AdvertisementRepository.create(
            session,
            group_id=group.id,
            user_id=user.id,
            telegram_message_id=556677,
            text="Sotiladi yangi moshina",
            score=85,
            status="DETECTED"
        )
        assert ad.id is not None
        ad_id = ad.id

        # Update Ad
        updated_ad = await AdvertisementRepository.update_ad(
            session,
            ad_id,
            status="APPROVED",
            risk_score=20,
            detection_reason="Manual verification",
            text="Tahrirlangan xabar"
        )
        assert updated_ad.status == "APPROVED"
        assert updated_ad.risk_score == 20
        assert updated_ad.text == "Tahrirlangan xabar"

        # Create Warning
        warn = await WarningRepository.create(
            session,
            user_id=user.id,
            group_id=group.id,
            advertisement_id=ad_id,
            warning_type="warning"
        )
        assert warn.id is not None
        warn_id = warn.id

        # Update Warning
        updated_warn = await WarningRepository.update_warning(session, warn_id, "mute_1h")
        assert updated_warn.warning_type == "mute_1h"

        # Delete Warning
        w_del = await WarningRepository.delete_by_id(session, warn_id)
        assert w_del is True
        assert (await WarningRepository.get_by_id(session, warn_id)) is None

        # Delete Ad
        ad_del = await AdvertisementRepository.delete_by_id(session, ad_id)
        assert ad_del is True
        assert (await AdvertisementRepository.get_by_id(session, ad_id)) is None

        # Clean up
        await GroupRepository.delete_by_id(session, group.id)
        await UserRepository.delete_by_id(session, user.id)
