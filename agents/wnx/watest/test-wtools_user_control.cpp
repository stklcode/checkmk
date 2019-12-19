// test-wtools.cpp
// windows mostly

#include "pch.h"

#include <Ntsecapi.h>

#include "common/wtools_user_control.h"
#include "logger.h"

namespace wtools::uc {  // to become friendly for cma::cfg classes

//
//
static const int counter = 0;

// List of all domains!!!
// This is #REFERENCE
NTSTATUS PrintDomainName() {
    LSA_HANDLE policy;

    static LSA_OBJECT_ATTRIBUTES oa = {sizeof(oa)};

    auto status = LsaOpenPolicy(0, &oa, POLICY_VIEW_LOCAL_INFORMATION, &policy);

    if (!LSA_SUCCESS(status)) return status;
    ON_OUT_OF_SCOPE(LsaClose(policy));

    // I do not know why we use union
    union {
        PPOLICY_DNS_DOMAIN_INFO ppddi;
        PPOLICY_ACCOUNT_DOMAIN_INFO ppadi;
    };

    status = LsaQueryInformationPolicy(policy, PolicyDnsDomainInformation,
                                       (void**)&ppddi);

    if (!LSA_SUCCESS(status)) return status;

    if (ppddi->Sid) {
        XLOG::l("DnsDomainName: '{}'",
                wtools::ConvertToUTF8(ppddi->DnsDomainName.Buffer));
    } else {
        XLOG::l("'{}': not domain controller !!",
                wtools::ConvertToUTF8(ppddi->Name.Buffer));
        status = -1;
    }

    LsaFreeMemory(ppddi);
    if (0 <= status) return status;

    if (LSA_SUCCESS(
            status = LsaQueryInformationPolicy(
                policy, PolicyAccountDomainInformation, (void**)&ppadi))) {
        XLOG::l("DomainName: '{}'",
                wtools::ConvertToUTF8(ppadi->DomainName.Buffer));
        LsaFreeMemory(ppadi);
    }

    return status;
}

TEST(WtoolsUserControl, Base) {
    LdapControl lc;
    ASSERT_TRUE(lc.name() == nullptr);
    auto ret = lc.chooseDomain(L"SERG-DELL", L"SERG-DELL");
    if (ret == Status::no_domain_service) {
        XLOG::SendStringToStdio("No Domain Controller - no testing\n",
                                XLOG::Colors::yellow);

        return;
    }
    ASSERT_TRUE(ret == Status::success);
}

TEST(WtoolsUserControl, AddDeleteUser) {
    LdapControl lc;
    std::wstring_view u = L"x_test_user";
    lc.UserDel(u);
    ON_OUT_OF_SCOPE(lc.UserDel(u));
    EXPECT_EQ(Status::absent, lc.UserDel(u));
    EXPECT_EQ(Status::success, lc.UserAdd(u, L"xufdrgebd_1"));
    EXPECT_EQ(Status::exists, lc.UserAdd(u, L"xufdrgebd_1"));
    EXPECT_EQ(Status::success, lc.UserDel(u));
    EXPECT_EQ(Status::absent, lc.UserDel(u));
}

TEST(WtoolsUserControl, AddDeleteUserToUsers) {
    LdapControl lc;
    std::wstring_view g = L"Users";
    std::wstring_view u = L"x_user_name";
    ASSERT_EQ(Status::success, lc.UserAdd(u, L"aaaaasxwxwwxwecfwecwe"));
    EXPECT_EQ(Status::success, lc.LocalGroupAddMembers(g, u));
    EXPECT_EQ(Status::success, lc.LocalGroupDelMembers(g, u));
    EXPECT_EQ(Status::absent, lc.LocalGroupDelMembers(g, u));

    EXPECT_EQ(Status::success, lc.LocalGroupAddMembers(g, u));
    EXPECT_EQ(Status::error, lc.LocalGroupDel(g));
    ASSERT_EQ(Status::success, lc.UserDel(u));
    EXPECT_EQ(Status::error, lc.LocalGroupDel(g));
}

TEST(WtoolsUserControl, AddDeleteCheckGroup) {
    LdapControl lc;
    std::wstring_view g = L"x_test_group";
    std::wstring_view c = L"Check MK Testing Group";
    lc.LocalGroupDel(g);
    ON_OUT_OF_SCOPE(lc.LocalGroupDel(g));
    EXPECT_EQ(Status::absent, lc.LocalGroupDel(g));
    EXPECT_EQ(Status::success, lc.LocalGroupAdd(g, c));
    EXPECT_EQ(Status::exists, lc.LocalGroupAdd(g, c));
    EXPECT_EQ(Status::success, lc.LocalGroupDel(g));
    EXPECT_EQ(Status::absent, lc.LocalGroupDel(g));
}

TEST(WtoolsUserControl, AddDeleteCheckForbiddenGroup) {
    using namespace std::literals::string_literals;
    LdapControl lc;
    static const std::wstring groups[] = {
        L"Access Control Assistance Operators"s,
        L"Administrators"s,
        L"Backup Operators"s,
        L"Cryptographic Operators"s,
        L"Device Owners"s,
        L"Distributed COM Users"s,
        L"Event Log Readers"s,
        L"Guests"s,
        L"Hyper-V Administrators"s,
        L"IIS_IUSRS"s,
        L"Network Configuration Operators"s,
        L"Performance Log Users"s,
        L"Performance Monitor Users"s,
        L"Power Users"s,
        L"Remote Desktop Users"s,
        L"Remote Management Users"s,
        L"Replicator"s,
        L"System Managed Accounts Group"s,
        L"Users"s};
    for (auto& g : groups) {
        //
        EXPECT_EQ(Status::error, lc.LocalGroupDel(g));
    }
}

TEST(WtoolsUserControl, AddDeleteMembers) {
    LdapControl lc;
    std::wstring_view g = L"x_test_group";
    std::wstring_view u = L"x_user_name";
    std::wstring_view c = L"Check MK Testing Group";
    lc.LocalGroupDel(g);
    ON_OUT_OF_SCOPE(lc.UserDel(u); lc.LocalGroupDel(g));

    EXPECT_EQ(Status::absent, lc.LocalGroupDel(g));
    EXPECT_EQ(Status::error, lc.LocalGroupAddMembers(g, u));

    ASSERT_EQ(Status::success, lc.LocalGroupAdd(g, c));
    EXPECT_EQ(Status::error, lc.LocalGroupAddMembers(g, u));
    ASSERT_EQ(Status::success, lc.UserAdd(u, L"aaaaasxwxwwxwecfwecwe"));
    EXPECT_EQ(Status::success, lc.LocalGroupAddMembers(g, u));

    EXPECT_EQ(Status::success, lc.LocalGroupDelMembers(g, u));
    EXPECT_EQ(Status::absent, lc.LocalGroupDelMembers(g, u));

    EXPECT_EQ(Status::success, lc.LocalGroupAddMembers(g, u));
    EXPECT_EQ(Status::success, lc.LocalGroupDel(g));
    ASSERT_EQ(Status::success, lc.UserDel(u));
    EXPECT_EQ(Status::absent, lc.LocalGroupDel(g));
}

}  // namespace wtools::uc
