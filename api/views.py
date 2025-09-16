from django.shortcuts import render
from rest_framework import viewsets
from loans.models import LoanAccount, Guarantor, LoanRepayment
from .serializers import LoanAccountSerializer, GuarantorSerializer, LoanRepaymentSerializer
from users.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import action
from rest_framework.decorators import api_view



class LoanAccountViewSet(viewsets.ModelViewSet):
    queryset = LoanAccount.objects.all()
    serializer_class = LoanAccountSerializer


    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        loan = self.get_object()
        action = request.data.get('action', '').lower()
        reason = request.data.get('reason', '')

        if loan.loan_status != 'PENDING_MANAGER':
            return Response({"error": "Loan is not pending manager approval."}, status=400)

        if action == 'approve':
            loan.loan_status = 'APPROVED'
            notification = "Your loan has been approved. Funds will be sent shortly."
        elif action == 'reject':
            loan.loan_status = 'REJECTED'
            loan.rejection_reason = reason
            notification = f"Your loan was rejected. Reason: {reason}"
        else:
            return Response({"error": "Action must be 'approve' or 'reject'"}, status=400)

        loan.approved_at = timezone.now()
        loan.save()

        return Response({
            "message": f"Loan {action}ed successfully.",
            "notification": notification,
            "status": loan.loan_status
        })

class GuarantorViewSet(viewsets.ModelViewSet):
    queryset = Guarantor.objects.all()
    serializer_class = GuarantorSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        guarantor = self.get_queryset().get(id=response.data['id'])
        
        notification_msg = (
            f"You’ve been requested to guarantee a loan of KES {guarantor.loan.requested_amount:,.2f} "
            f"for {guarantor.loan.member.first_name}. Please respond in the app."
        )
        
        response.data['notification'] = notification_msg
        return response

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        guarantor = self.get_object()
        action = request.data.get('action', '').lower()

        if action not in ['approve', 'reject']:
            return Response({"error": "Action must be 'approve' or 'reject'"}, status=400)

        if guarantor.status != 'Pending':
            return Response({"error": "Already responded or expired."}, status=400)

        if action == 'approve':
            guarantor.status = 'Approved'
        else:
            guarantor.status = 'Rejected'
        guarantor.responded_at = timezone.now()
        guarantor.save()

        if action == 'approve':
            loan = guarantor.loan
            loan.loan_status = 'PENDING_MANAGER'
            loan.save()

        if action == 'reject':
            msg = f"Your guarantor {guarantor.guarantor_name} rejected your loan. Add a new one."
        else:
            msg = f"{guarantor.guarantor_name} approved your loan. Waiting for manager."

        return Response({
            "message": f"Guarantor request {action}ed.",
            "notification": msg,
            "status": guarantor.status
        })

    @action(detail=True, methods=['get'])
    def check_status(self, request, pk=None):
        guarantor = self.get_object()
        data = {
            "id": guarantor.id,
            "loan_id": guarantor.loan.id,
            "guarantor_name": guarantor.guarantor_name,
            "status": guarantor.status,
            "created_at": guarantor.created_at,
            "responded_at": guarantor.responded_at,
        }

        if guarantor.status == 'Expired':
            data["notification"] = (
                f"Your guarantor request for '{guarantor.guarantor_name}' has expired. "
                f"Please add a new guarantor for your loan (ID: {guarantor.loan.id})."
            )

        return Response(data)


@api_view(['POST'])
def expire_guarantors_manual(request):
    expired_count = Guarantor.objects.filter(
        status='Pending',
        created_at__lt=timezone.now() - timedelta(hours=24)
    ).update(
        status='Expired',
        updated_at=timezone.now()
    )

    return Response({
        "message": f"Successfully expired {expired_count} guarantor request(s).",
        "status": "success"
    })

class LoanRepaymentViewSet(viewsets.ModelViewSet):
    queryset = LoanRepayment.objects.all()
    serializer_class = LoanRepaymentSerializer




 

